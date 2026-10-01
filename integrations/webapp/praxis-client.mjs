/** Framework-neutral client. Keep this instance/token in memory, never localStorage. */
export class PraxisClient {
  #token = null;
  constructor(baseURL) {
    this.base = new URL(baseURL);
    if (this.base.protocol !== "https:") throw new Error("Trusted HTTPS is required");
    if (this.base.username || this.base.password) throw new Error("Credentials do not belong in URLs");
  }
  async request(path, body) {
    const headers = {};
    if (this.#token) headers.Authorization = `Bearer ${this.#token}`;
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const response = await fetch(new URL(path, this.base), {
      method: body === undefined ? "GET" : "POST", headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: "omit", cache: "no-store", redirect: "error"
    });
    if (!response.ok) {
      if (response.status === 401) this.#token = null;
      throw new Error(`Praxis request failed (${response.status})`);
    }
    return response.json();
  }
  async login(username, password, tenant_id) {
    this.#token = null;
    const result = await this.request("/api/v1/auth/login", {username, password, tenant_id});
    this.#token = result.access_token;
  }
  logout() { this.#token = null; }
  health() { return this.request("/api/v2/health"); }
  startSession(tenant_id, call_id, host_app_id) {
    return this.request("/api/v1/sessions", {
      tenant_id, call_id, host_app_id, created_at: new Date().toISOString()
    });
  }
  endSession(id) { return this.request(`/api/v1/sessions/${encodeURIComponent(id)}/end`, {}); }
  analyze(session_id, pcm16kMono) {
    if (!(pcm16kMono instanceof Float32Array) || pcm16kMono.length < 16000 ||
        pcm16kMono.length > 120 * 16000) throw new Error("Expected 1-120 seconds of mono 16kHz Float32 PCM");
    const bytes = new Uint8Array(pcm16kMono.length * 4);
    const view = new DataView(bytes.buffer);
    for (let i = 0; i < pcm16kMono.length; i++) {
      if (!Number.isFinite(pcm16kMono[i])) throw new Error("Non-finite audio");
      view.setFloat32(i * 4, pcm16kMono[i], true);
    }
    let binary = "";
    for (let i = 0; i < bytes.length; i += 8192)
      binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
    return this.request("/api/v2/analysis", {
      session_id, pcm_f32le_base64: btoa(binary), sample_rate: 16000, channels: 1
    });
  }
}
