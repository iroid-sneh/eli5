import { NextResponse } from 'next/server';

const mockTodos = [
  { id: 1, title: 'Buy milk', done: false },
  { id: 2, title: 'Walk dog', done: true },
];

export async function GET() {
  return NextResponse.json(mockTodos);
}

export async function POST(req: Request) {
  const body = await req.json();
  // TODO: save to the database instead of memory
  mockTodos.push({ id: Date.now(), title: body.title, done: false });
  return NextResponse.json({ ok: true });
}
