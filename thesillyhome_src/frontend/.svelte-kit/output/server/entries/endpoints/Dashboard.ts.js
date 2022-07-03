import { readFileSync } from "fs";
const config_file_path = "./data/metrics_matrix.json";
async function get(request) {
  const data = readFileSync(config_file_path, "utf-8");
  const json_data = JSON.parse(data);
  return { body: { metrics: json_data } };
}
export { get };
