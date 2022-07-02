import { statSync } from 'fs'

export async function get(request) {
    const stats = statSync(request.url.searchParams.get('path'));
    const mtime = stats.mtime;
    return mtime;
}