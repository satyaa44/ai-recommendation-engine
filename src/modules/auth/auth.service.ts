import { Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { UsersService } from '../users/users.service';
import { CreateUserDto } from '../users/dto/create-user.dto';

@Injectable()
export class AuthService {
  constructor(
    private usersService: UsersService,
    private jwtService: JwtService,
  ) {}

  async register(createUserDto: CreateUserDto) {
    try {
      const user = await this.usersService.create(createUserDto);
      return this.generateTokens(user.id, user.email);
    } catch (error) {
      throw new UnauthorizedException(error.message);
    }
  }

  async login(email: string, password: string) {
    const user = await this.usersService.findByEmail(email);

    if (!user) {
      throw new UnauthorizedException('Invalid email or password');
    }

    const isPasswordValid = await this.usersService.validatePassword(
      password,
      user.password,
    );

    if (!isPasswordValid) {
      throw new UnauthorizedException('Invalid email or password');
    }

    return this.generateTokens(user.id, user.email);
  }

  async validateUser(userId: string, email: string) {
    try {
      const user = await this.usersService.findOne(userId);
      if (user && user.email === email) {
        return user;
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  private generateTokens(userId: string, email: string) {
    const payload = { sub: userId, email };

    const accessToken = this.jwtService.sign(payload, {
      expiresIn: process.env.JWT_EXPIRATION || '24h',
    });

    const refreshToken = this.jwtService.sign(payload, {
      secret: process.env.JWT_REFRESH_SECRET || 'refresh_secret_key',
      expiresIn: process.env.JWT_REFRESH_EXPIRATION || '7d',
    });

    return {
      accessToken,
      refreshToken,
      userId,
      email,
      expiresIn: '24h',
    };
  }
}
