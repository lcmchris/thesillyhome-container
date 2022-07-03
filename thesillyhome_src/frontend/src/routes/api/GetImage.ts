import { readFileSync } from 'fs'

export async function get(request) {
    const data = readFileSync(request.url.searchParams.get('path'), 'base64')
    return { body: { message: data } };
}