import { getStats } from '../../lib/stats';

export default async function Dashboard() {
  const stats = await getStats();
  return <div>Done: {stats.done} / {stats.total}</div>;
}
