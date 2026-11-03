import { settings } from "./config";
import { authorized } from "./auth";
export function audit(token: string, payload: string) {
  if (settings.requireAuth && !authorized(token)) throw new Error("denied");
  const endpoint = settings.endpoint;
  return fetch(endpoint, { method: "POST", body: payload });
}
export function secret() {
  const token = process.env.SYNTHETIC_TOKEN;
  return token;
}
