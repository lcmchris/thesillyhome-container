import { writeFileSync } from 'fs'

const config_file_path = '/thesillyhome_src/frontend/static/data/metrics_matrix.json'

export async function post({ request }) {
    const data = await request.json()
    writeFileSync(config_file_path, JSON.stringify(data), 'utf-8')
    return { body: { message: 'success' } };

}