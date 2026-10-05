import praxisLogo from './assets/praxis-logo.png?inline';

/** Minimal branding/host adaptations to the registered, unmodified HTML source. */
export function praxisWaterSource(source: string) {
  return source
    // Warm the water and highlights while preserving the original logo texture.
    .replace('vec3(0.006, 0.030, 0.055)', 'vec3(0.055, 0.026, 0.006)')
    .replace('vec3(0.012, 0.078, 0.125)', 'vec3(0.125, 0.059, 0.012)')
    .replace('vec3(0.02, 0.10, 0.13)', 'vec3(0.13, 0.066, 0.02)')
    .replace('vec3(0.55, 0.92, 1.0)', 'vec3(1.0, 0.738, 0.55)')
    .replace('vec3(0.95, 1.0, 1.0)', 'vec3(1.0, 0.971, 0.95)')
    .replace('vec3(0.09, 0.30, 0.40)', 'vec3(0.40, 0.219, 0.09)')
    .replace('vec3(0.25, 0.55, 0.65)', 'vec3(0.65, 0.417, 0.25)')
    .replace('vec3(0.65, 0.9, 1.0)', 'vec3(1.0, 0.796, 0.65)')
    .replace('<h2>OpenAI</h2>', '<h2>Praxis</h2>')
    .replace("'use strict';", `'use strict';\n(async () => {\nconst praxisImage = new Image();\npraxisImage.src = ${JSON.stringify(praxisLogo)};\nawait praxisImage.decode();`)
    .replace('openai: buildLogo(LOGO_PATHS.openai),', `praxis: (() => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = SDF_SIZE;
    const ctx = canvas.getContext('2d');
    const scale = SDF_SIZE * 0.60 / Math.max(praxisImage.width, praxisImage.height);
    const width = praxisImage.width * scale, height = praxisImage.height * scale;
    ctx.drawImage(praxisImage, (SDF_SIZE - width) / 2, (SDF_SIZE - height) / 2, width, height);
    const image = ctx.getImageData(0, 0, SDF_SIZE, SDF_SIZE);
    return { sdf: buildSDF(image), edges: edgePoints(image), image };
  })(),`)
    .replace('FRAG_WATER, logos.openai,', 'FRAG_WATER, logos.praxis,')
    .replace('this.aspect = w / h;', `this.aspect = w / h;
    // Center the desktop mark between the introduction and sign-in card.
    if (this.opts.sim) {
      const markY = 200 + Math.max(190, Math.min(326, r.width * 0.38)) / 2;
      this.opts.shift = r.width <= 860 ? [0, 0.5 - markY / r.height] : [-0.04, 0];
    }`)
    .replace('uniform vec2 uSimTexel;', 'uniform vec2 uSimTexel;\nuniform sampler2D uMark;')
    .replace('col += markCol * (logo * 0.92 + glow);', `vec2 markUV = 0.5 + (ruv - 0.5 - uShift) * uScale;
  vec4 mark = texture(uMark, vec2(markUV.x, 1.0 - markUV.y));
  col += mark.rgb * mark.a * 0.92 + markCol * glow;`)
    .replace('// particle system', `// Praxis color texture follows the same refracted coordinates as the authored SDF.
    if (logo.image) {
      this.markTex = gl.createTexture();
      gl.activeTexture(gl.TEXTURE2);
      gl.bindTexture(gl.TEXTURE_2D, this.markTex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, logo.image);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.useProgram(this.prog);
      gl.uniform1i(gl.getUniformLocation(this.prog, 'uMark'), 2);
      gl.activeTexture(gl.TEXTURE0);
    }

    // particle system`)
    .replace('const t0 = performance.now();', `// Forward host pointer positions without putting an iframe over the login fields.
window.addEventListener('message', event => {
  if (event.source !== parent || event.data?.type !== 'praxis-water-pointer') return;
  const { kind, x, y } = event.data;
  if (!['pointermove', 'pointerdown', 'pointerup', 'pointerleave'].includes(kind)) return;
  if (!Number.isFinite(x) || !Number.isFinite(y)) return;
  document.querySelector('[data-fx="water"]').dispatchEvent(new PointerEvent(kind, {
    clientX: x * innerWidth, clientY: y * innerHeight,
  }));
});
const t0 = performance.now();`)
    .replace('</script>\n</body>', `})().catch(error => {
  console.error('Praxis water background failed to initialize', error);
});\n</script>\n</body>`);
}
