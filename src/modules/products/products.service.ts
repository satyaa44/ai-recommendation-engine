import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Product } from './entities/product.entity';
import { CreateProductDto } from './dto/create-product.dto';
import { UpdateProductDto } from './dto/update-product.dto';

@Injectable()
export class ProductsService {
  constructor(
    @InjectRepository(Product)
    private productsRepository: Repository<Product>,
  ) {}

  async create(createProductDto: CreateProductDto): Promise<Product> {
    const product = this.productsRepository.create(createProductDto);
    return this.productsRepository.save(product);
  }

  async findOne(id: string): Promise<Product> {
    const product = await this.productsRepository.findOne({ where: { id } });
    if (!product) {
      throw new Error(`Product with ID ${id} not found`);
    }
    return product;
  }

  async findAll(skip = 0, take = 20): Promise<{ data: Product[]; total: number }> {
    const [data, total] = await this.productsRepository.findAndCount({
      skip,
      take,
      order: { createdAt: 'DESC' },
    });
    return { data, total };
  }

  async search(query: string, skip = 0, take = 20): Promise<{ data: Product[]; total: number }> {
    const [data, total] = await this.productsRepository
      .createQueryBuilder('product')
      .where('product.name ILIKE :query', { query: `%${query}%` })
      .orWhere('product.description ILIKE :query', { query: `%${query}%` })
      .orWhere('product.category ILIKE :query', { query: `%${query}%` })
      .skip(skip)
      .take(take)
      .orderBy('product.rating', 'DESC')
      .getManyAndCount();

    return { data, total };
  }

  async findByCategory(category: string, skip = 0, take = 20): Promise<{ data: Product[]; total: number }> {
    const [data, total] = await this.productsRepository.findAndCount({
      where: { category },
      skip,
      take,
      order: { rating: 'DESC' },
    });
    return { data, total };
  }

  async getTrending(limit = 10): Promise<Product[]> {
    return this.productsRepository
      .createQueryBuilder('product')
      .orderBy('product.viewCount', 'DESC')
      .limit(limit)
      .getMany();
  }

  async update(id: string, updateProductDto: UpdateProductDto): Promise<Product> {
    const product = await this.findOne(id);
    Object.assign(product, updateProductDto);
    return this.productsRepository.save(product);
  }

  async incrementViewCount(id: string): Promise<void> {
    await this.productsRepository
      .createQueryBuilder()
      .update(Product)
      .set({ viewCount: () => 'viewCount + 1' })
      .where('id = :id', { id })
      .execute();
  }

  async incrementPurchaseCount(id: string): Promise<void> {
    await this.productsRepository
      .createQueryBuilder()
      .update(Product)
      .set({ purchaseCount: () => 'purchaseCount + 1' })
      .where('id = :id', { id })
      .execute();
  }

  async updateRating(id: string, newRating: number): Promise<Product> {
    const product = await this.findOne(id);
    product.rating = newRating;
    product.reviewCount += 1;
    return this.productsRepository.save(product);
  }

  async remove(id: string): Promise<void> {
    const product = await this.findOne(id);
    await this.productsRepository.remove(product);
  }
}
