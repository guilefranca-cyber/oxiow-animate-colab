# -*- coding: utf-8 -*-
"""
OXIOW — WAN 2.2 ANIMATE (V2V) no Kaggle grátis.
Troca a IDENTIDADE de um vídeo real pela Margaret, mantendo o movimento e a boca originais.

POR QUE ESTE KERNEL EXISTE (22-09-2026):
  Eu tentei consertar a BOCA depois de gerada (Wav2Lip, MuseTalk, LatentSync, EchoMimic)
  e a boca continuava "abrindo e fechando". O motivo é simples: o Wan 2.2 S2V NUNCA
  articulou fonema. O ANIMATE não inventa o movimento — ele COPIA de um vídeo real.
  A frase do tutorial do dono: "identity never comes from text, it comes from the
  reference images".

REGRA DO DONO: TUDO GRATUITO. Sem Seedance, sem MiniMax H3, sem API paga.
  GPU = T4 do Kaggle (30 h/semana). Modelos = Wan 2.2 Animate Q4_K_M (Apache-2.0).
"""
import os, sys, subprocess, shutil, glob, json, time

def sh(c, timeout=7200, quiet=False):
    p = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=timeout)
    out = (p.stdout or '') + (p.stderr or '')
    if not quiet:
        print('\n'.join(out.strip().splitlines()[-14:]))
    return p.returncode, out

print("=" * 70)
print("OXIOW — WAN 2.2 ANIMATE (V2V)")
print("=" * 70)

# ── 1. GPU ────────────────────────────────────────────────────────────────
rc, g = sh("nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader", quiet=True)
print("GPU:", g.strip())
print("VRAM livre:")
sh("nvidia-smi --query-gpu=memory.free --format=csv,noheader")

# ── 2. ENTRADA (dataset do Kaggle com o acervo) ───────────────────────────
ENTRADA = None
for cand in ["/kaggle/input/oxiow-animate-entrada", "/kaggle/input/oxiow-acervo-margaret"]:
    if os.path.isdir(cand):
        ENTRADA = cand; break
if not ENTRADA:
    achados = glob.glob("/kaggle/input/*")
    print("datasets montados:", achados)
    sys.exit("ERRO: dataset de entrada nao encontrado")

print("ENTRADA:", ENTRADA)
for f in sorted(glob.glob(ENTRADA + "/*"))[:20]:
    print(f"  {os.path.getsize(f)/1024/1024:8.2f} MB  {os.path.basename(f)}")

# ── 3. O WORKFLOW + OS MODELOS ────────────────────────────────────────────
W = "/kaggle/working/animate"
sh(f"mkdir -p {W}/models/{{diffusion_models,vae,text_encoders,sam2,loras,controlnet_aux}}")
sh(f"mkdir -p {W}/{{input,output}}")

MODELOS = {}
for raiz in (ENTRADA, "/kaggle/input/oxiow-wan22-gguf", "/kaggle/input/oxiow-s2v-aux"):
    if not os.path.isdir(raiz): continue
    for p in glob.glob(raiz + "/**/*", recursive=True):
        if os.path.isfile(p):
            MODELOS[os.path.basename(p)] = p
print(f"\n{len(MODELOS)} arquivos disponiveis nos datasets:")
for k in sorted(MODELOS)[:25]: print("  ", k)

# liga o que o ComfyUI pede (nomes do workflow nativo do Animate)
LIGA = {
 "Wan2.2-Animate-14B-Q4_K_M.gguf": "diffusion_models",
 "Wan2_2_Animate_14B_Q4_K_M.gguf": "diffusion_models",
 "wan_2.1_vae.safetensors": "vae",
 "Wan2.1_VAE.pth": "vae",
 "umt5_xxl_fp8_e4m3fn_scaled.safetensors": "text_encoders",
 "sam2_hiera_base_plus.safetensors": "sam2",
 "Wan21_I2V_14B_lightx2v_cfg_step_distill_lora_rank64.safetensors": "loras",
 "dw-ll_ucoco_384_bs5.torchscript.pt": "controlnet_aux",
 "yolox_l.torchscript.pt": "controlnet_aux",
}
for nome, sub in LIGA.items():
    if nome in MODELOS:
        sh(f"ln -sfn '{MODELOS[nome]}' {W}/models/{sub}/{nome}")
        print(f"  ligado: {nome} -> {sub}/")

print("\nmodelos ligados:")
sh(f"ls -la {W}/models/diffusion_models/ {W}/models/vae/ {W}/models/text_encoders/ 2>/dev/null | grep -v '^total'")

# ── 4. O QUE FALTA (a lista honesta) ──────────────────────────────────────
FALTAM = [n for n in ("wan_2.1_vae.safetensors","umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                      "dw-ll_ucoco_384_bs5.torchscript.pt") if n not in MODELOS]
if FALTAM:
    print(f"\n⚠️  FALTAM {len(FALTAM)} arquivos: {FALTAM}")
    print("   (o ComfyUI baixa alguns sozinho no primeiro uso; os outros precisam de dataset)")
else:
    print("\n✅ todos os modelos necessarios estao nos datasets")

print("\n" + "=" * 70)
print("PRONTO PARA O COMFYUI. O proximo passo e subir o workflow pela API.")
print("=" * 70)
