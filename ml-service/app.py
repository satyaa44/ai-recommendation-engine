import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import pickle
import logging
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for models
user_item_matrix = None
product_features = None
user_profiles = None
similarity_matrix = None

# ============================================
# COLLABORATIVE FILTERING MODEL
# ============================================

class CollaborativeFilteringModel:
    """User-based collaborative filtering recommendation system"""
    
    def __init__(self):
        self.user_item_matrix = None
        self.similarity_matrix = None
        self.scaler = MinMaxScaler()
    
    def build_user_item_matrix(self, interactions):
        """
        Build user-item interaction matrix
        interactions: list of dicts with userId, productId, weight
        """
        try:
            df = pd.DataFrame(interactions)
            
            # Create pivot table (users x products)
            self.user_item_matrix = df.pivot_table(
                index='userId',
                columns='productId',
                values='weight',
                fill_value=0
            )
            
            # Normalize the matrix
            self.user_item_matrix = self.user_item_matrix.fillna(0)
            
            logger.info(f"User-Item Matrix built: {self.user_item_matrix.shape}")
            return True
        except Exception as e:
            logger.error(f"Error building user-item matrix: {str(e)}")
            return False
    
    def compute_similarity(self):
        """Compute user similarity using cosine similarity"""
        try:
            if self.user_item_matrix is None or len(self.user_item_matrix) == 0:
                return False
            
            # Calculate cosine similarity between users
            self.similarity_matrix = cosine_similarity(self.user_item_matrix)
            logger.info("User similarity matrix computed")
            return True
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return False
    
    def get_recommendations(self, user_id, n_recommendations=10, all_users=None):
        """
        Get recommendations for a user using collaborative filtering
        """
        try:
            if self.user_item_matrix is None or user_id not in self.user_item_matrix.index:
                # Return empty recommendations for new users
                return self._get_fallback_recommendations(n_recommendations)
            
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            
            # Get similar users (excluding the user itself)
            similar_users_idx = np.argsort(self.similarity_matrix[user_idx])[::-1][1:6]
            
            # Get items rated by similar users but not by current user
            user_rated_items = set(self.user_item_matrix.columns[self.user_item_matrix.iloc[user_idx] > 0])
            
            recommendations = {}
            for similar_idx in similar_users_idx:
                similar_user_id = self.user_item_matrix.index[similar_idx]
                similar_user_items = self.user_item_matrix.iloc[similar_idx]
                
                for product_id, rating in similar_user_items.items():
                    if product_id not in user_rated_items and rating > 0:
                        if product_id not in recommendations:
                            recommendations[product_id] = []
                        
                        # Weight by similarity score
                        weighted_score = rating * self.similarity_matrix[user_idx][similar_idx]
                        recommendations[product_id].append(weighted_score)
            
            # Average the scores
            final_scores = {
                product_id: np.mean(scores)
                for product_id, scores in recommendations.items()
            }
            
            # Sort and get top N
            top_recommendations = sorted(
                final_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:n_recommendations]
            
            return [
                {
                    'productId': str(product_id),
                    'score': float(score),
                    'algorithm': 'collaborative_filtering'
                }
                for product_id, score in top_recommendations
            ]
        
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return self._get_fallback_recommendations(n_recommendations)
    
    def _get_fallback_recommendations(self, n_recommendations):
        """Fallback recommendations for new users"""
        return []


# ============================================
# CONTENT-BASED MODEL
# ============================================

class ContentBasedModel:
    """Content-based filtering using product features"""
    
    def __init__(self):
        self.product_features = None
        self.user_profiles = None
    
    def build_product_features(self, products):
        """
        Build product feature matrix
        products: list of dicts with id, category, price, tags, etc.
        """
        try:
            features = {}
            
            for product in products:
                product_id = product.get('id')
                
                # Create feature vector
                feature_vector = {
                    'category': product.get('category', ''),
                    'price': float(product.get('price', 0)),
                    'rating': float(product.get('rating', 0)),
                    'tags': product.get('tags', []),
                }
                
                features[product_id] = feature_vector
            
            self.product_features = features
            logger.info(f"Product features built for {len(features)} products")
            return True
        
        except Exception as e:
            logger.error(f"Error building product features: {str(e)}")
            return False
    
    def build_user_profile(self, user_id, user_interactions, products):
        """Build user profile based on their interactions"""
        try:
            # Get user's liked products
            liked_products = [
                int(interaction['productId']) 
                for interaction in user_interactions 
                if interaction.get('weight', 0) > 5
            ]
            
            if not liked_products:
                return None
            
            # Extract common features from liked products
            categories = []
            avg_price = []
            avg_rating = []
            
            for product in products:
                if product.get('id') in liked_products:
                    categories.extend(product.get('tags', []))
                    avg_price.append(float(product.get('price', 0)))
                    avg_rating.append(float(product.get('rating', 0)))
            
            user_profile = {
                'userId': user_id,
                'preferred_categories': list(set(categories)),
                'avg_price_preference': np.mean(avg_price) if avg_price else 0,
                'min_rating_preference': np.mean(avg_rating) if avg_rating else 0,
            }
            
            return user_profile
        
        except Exception as e:
            logger.error(f"Error building user profile: {str(e)}")
            return None
    
    def get_recommendations(self, user_profile, all_products, n_recommendations=10):
        """Get content-based recommendations"""
        try:
            if not user_profile or not self.product_features:
                return []
            
            recommendations = []
            
            for product in all_products:
                product_id = product.get('id')
                
                # Skip if in user's preferred categories
                product_tags = set(product.get('tags', []))
                preferred_categories = set(user_profile.get('preferred_categories', []))
                
                # Calculate similarity score
                category_match = len(product_tags & preferred_categories) / (len(product_tags) + 1)
                price_match = 1 - abs(float(product.get('price', 0)) - user_profile['avg_price_preference']) / 1000
                rating_match = float(product.get('rating', 0)) / 5.0
                
                # Weighted score
                score = (category_match * 0.4) + (price_match * 0.3) + (rating_match * 0.3)
                
                if score > 0:
                    recommendations.append({
                        'productId': str(product_id),
                        'score': float(score),
                        'algorithm': 'content_based'
                    })
            
            # Sort and return top N
            return sorted(
                recommendations,
                key=lambda x: x['score'],
                reverse=True
            )[:n_recommendations]
        
        except Exception as e:
            logger.error(f"Error getting content-based recommendations: {str(e)}")
            return []


# ============================================
# HYBRID MODEL
# ============================================

def hybrid_recommendations(cf_recs, cb_recs, cf_weight=0.6, cb_weight=0.4):
    """Combine collaborative and content-based recommendations"""
    try:
        combined = {}
        
        # Add CF recommendations
        for rec in cf_recs:
            product_id = rec['productId']
            combined[product_id] = {
                'score': rec['score'] * cf_weight,
                'algorithm': 'hybrid',
                'cf_score': rec['score'],
                'cb_score': 0
            }
        
        # Add CB recommendations
        for rec in cb_recs:
            product_id = rec['productId']
            if product_id in combined:
                combined[product_id]['score'] += rec['score'] * cb_weight
                combined[product_id]['cb_score'] = rec['score']
            else:
                combined[product_id] = {
                    'score': rec['score'] * cb_weight,
                    'algorithm': 'hybrid',
                    'cf_score': 0,
                    'cb_score': rec['score']
                }
        
        # Sort by score
        sorted_recs = sorted(
            combined.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        return [
            {
                'productId': product_id,
                'score': float(rec['score']),
                'algorithm': rec['algorithm'],
            }
            for product_id, rec in sorted_recs
        ]
    
    except Exception as e:
        logger.error(f"Error in hybrid recommendations: {str(e)}")
        return []


# ============================================
# FLASK ROUTES
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'ml-recommendation-engine',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/recommend', methods=['POST'])
def get_recommendations():
    """Main recommendation endpoint"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        limit = data.get('limit', 10)
        interactions = data.get('interactions', [])
        products = data.get('products', [])
        
        if not user_id:
            return jsonify({'error': 'userId required'}), 400
        
        # Initialize models
        cf_model = CollaborativeFilteringModel()
        cb_model = ContentBasedModel()
        
        # Build matrices
        if interactions:
            cf_model.build_user_item_matrix(interactions)
            cf_model.compute_similarity()
        
        if products:
            cb_model.build_product_features(products)
        
        # Get recommendations from both models
        cf_recs = cf_model.get_recommendations(user_id, limit) if interactions else []
        
        user_profile = None
        cb_recs = []
        if products and interactions:
            user_profile = cb_model.build_user_profile(user_id, interactions, products)
            if user_profile:
                cb_recs = cb_model.get_recommendations(user_profile, products, limit)
        
        # Combine recommendations
        if cf_recs and cb_recs:
            final_recs = hybrid_recommendations(cf_recs, cb_recs)
        elif cf_recs:
            final_recs = cf_recs
        elif cb_recs:
            final_recs = cb_recs
        else:
            # Fallback: return random popular products
            final_recs = [
                {
                    'productId': str(p.get('id')),
                    'score': float(p.get('rating', 0)) / 5.0,
                    'algorithm': 'popularity'
                }
                for p in products[:limit]
            ]
        
        return jsonify({
            'userId': user_id,
            'recommendations': final_recs[:limit],
            'count': len(final_recs),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in /recommend: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/train', methods=['POST'])
def train_model():
    """Train/update recommendation models"""
    try:
        data = request.get_json()
        interactions = data.get('interactions', [])
        products = data.get('products', [])
        
        # Train models
        cf_model = CollaborativeFilteringModel()
        cb_model = ContentBasedModel()
        
        cf_success = cf_model.build_user_item_matrix(interactions) and cf_model.compute_similarity()
        cb_success = cb_model.build_product_features(products)
        
        return jsonify({
            'status': 'trained',
            'collaborative_filtering': cf_success,
            'content_based': cb_success,
            'interactions_count': len(interactions),
            'products_count': len(products),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in /train: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/evaluate', methods=['POST'])
def evaluate_recommendations():
    """Evaluate recommendation quality (CTR, Conversion)"""
    try:
        data = request.get_json()
        recommendations = data.get('recommendations', [])
        clicks = data.get('clicks', 0)
        purchases = data.get('purchases', 0)
        
        if not recommendations:
            return jsonify({'error': 'recommendations required'}), 400
        
        ctr = (clicks / len(recommendations)) if recommendations else 0
        conversion_rate = (purchases / clicks) if clicks > 0 else 0
        
        return jsonify({
            'total_recommendations': len(recommendations),
            'clicks': clicks,
            'purchases': purchases,
            'ctr': float(ctr),
            'conversion_rate': float(conversion_rate),
            'avg_score': float(np.mean([r.get('score', 0) for r in recommendations])),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in /evaluate: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/similar-products', methods=['POST'])
def get_similar_products():
    """Get products similar to a given product"""
    try:
        data = request.get_json()
        product_id = data.get('productId')
        all_products = data.get('products', [])
        limit = data.get('limit', 5)
        
        if not product_id or not all_products:
            return jsonify({'error': 'productId and products required'}), 400
        
        # Find the reference product
        reference_product = None
        for p in all_products:
            if str(p.get('id')) == str(product_id):
                reference_product = p
                break
        
        if not reference_product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Find similar products
        similar = []
        ref_tags = set(reference_product.get('tags', []))
        ref_category = reference_product.get('category', '')
        
        for p in all_products:
            if str(p.get('id')) == str(product_id):
                continue
            
            # Calculate similarity
            tags_match = len(ref_tags & set(p.get('tags', []))) / (len(ref_tags) + 1)
            category_match = 1.0 if p.get('category') == ref_category else 0.3
            
            score = (tags_match * 0.6) + (category_match * 0.4)
            
            similar.append({
                'productId': str(p.get('id')),
                'name': p.get('name', ''),
                'score': float(score),
                'algorithm': 'content_similarity'
            })
        
        # Sort and return top N
        result = sorted(similar, key=lambda x: x['score'], reverse=True)[:limit]
        
        return jsonify({
            'referenceProductId': str(product_id),
            'similar_products': result,
            'count': len(result),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in /similar-products: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = os.getenv('FLASK_PORT', 5000)
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=int(port), debug=debug)
