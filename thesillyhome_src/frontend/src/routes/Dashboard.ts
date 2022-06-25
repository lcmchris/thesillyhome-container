import { readFileSync } from 'fs'

const config_file_path = '/thesillyhome_src/data/model/Base_0.0.0/metrics_matrix.json'

export async function get(request) {
    const data = readFileSync(config_file_path, 'utf-8')
    const json_data = JSON.parse(data)
    return { body: { metrics: json_data } };
}