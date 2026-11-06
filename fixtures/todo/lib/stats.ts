import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient({ datasources: { db: { url: process.env.DATABASE_URL } } });

export async function getStats() {
  try {
    const total = await prisma.todo.count();
    const done = await prisma.todo.count({ where: { done: true } });
    return { total, done };
  } catch (e) {}
  return { total: 0, done: 0 };
}
