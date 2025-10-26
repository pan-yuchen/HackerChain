import json, os
import requests
from openai import OpenAI
import base64

# --------------------
# 1) 调用文本模型（生成 branding JSON）
# --------------------
def generate_branding(client, idea):
    # 你可以把下面的 system/user prompt 替换为你现有的 prompt 模板
    completion = client.chat.completions.create(
        extra_body={},
        model="openai/gpt-5",
        messages=[
            {
                "role": "system",
                "content": [
                    {"type": "text", "text":
                        (
                            "You are a creative branding assistant. Given a startup idea, produce a concise branding package. "
                            "IMPORTANT: Respond ONLY with a single valid JSON object (no extra prose). "
                            "The JSON must contain these keys: "
                            "\"company_name\", \"tagline\", \"promotional_copy\", \"poster\". "
                            "\"promotional_copy\" should be an object with keys \"short\" and \"long\". "
                            "\"poster\" should be an object with keys: "
                            "\"palette\" (a list of {name, hex} color objects), "
                            "\"style\" (one-line style descriptor), and "
                            "\"layout_instructions\" (2-3 short bullet-like sentences for a designer). "
                            "Keep promotional copy friendly, 2-3 words max. "
                            "Do NOT include markdown, explanations, or any trailing text — only JSON."
                        )
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Here is the startup idea. Produce the branding package as specified above.\n\nIdea: {idea}\n\nRequired language: return text in the same language as the input idea."}
                ]
            }
        ]
    )

    raw = completion.choices[0].message.content
    # 尝试解析 JSON
    try:
        data = json.loads(raw)
        return data, raw
    except Exception as e:
        # 如果解析失败，返回 None 并把 raw text 一并返回方便调试
        print("Warning: failed to parse JSON from branding model:", e)
        return None, raw

# --------------------
# 2) 将 branding 转成图像模型的 Prompt（字符串）
# --------------------
def build_image_prompt_from_branding(branding, fallback_raw_text=None):
    """
    branding: parsed JSON dict or None
    fallback_raw_text: 原始模型输出字符串（当 branding 为 None 时使用）
    """
    if branding is None:
        # 直接使用原始文本作为 prompt（最简回退方案）
        return ("Use the following brief to design a poster:\n\n" + (fallback_raw_text or "No branding data available."))

    # 从 JSON 中提取字段（做好容错）
    company = branding.get("company_name", "Unnamed Company")
    tagline = branding.get("tagline", "")
    promo = branding.get("promotional_copy", {})
    promo_short = promo.get("short", "")
    promo_long = promo.get("long", "")
    poster = branding.get("poster", {})
    palette = poster.get("palette", [])  # 期待: [{'name':'warm yellow','hex':'#F4D9A9'}, ...]
    style = poster.get("style", "")
    layout = poster.get("layout_instructions", "")

    # 构造颜色描述字符串（包含 hex）
    palette_str = ", ".join([f"{c.get('name','') or 'color'} ({c.get('hex','')})" for c in palette])

    # 构造最优质的图像模型 prompt（尽量具体）
    prompt_lines = [
        f"Design a high-resolution poster for the brand: \"{company}\".",
        f"Tagline (display prominently): \"{tagline}\"." if tagline else "",
        "Main text to include on the poster:",
        f"- Short headline: {promo_short}",
        f"- Supporting copy: {promo_long}",
        "",
        "Visual style instructions:",
        f"- Style: {style}" if style else "- Style: modern, clean",
        f"- Color palette (use these exact hex codes when possible): {palette_str}" if palette_str else "",
        "",
        "Layout & composition:",
        f"- {layout}" if layout else "- Use large headline at top, central hero image, call-to-action at bottom.",
        "",
        "Technical requirements:",
        "- Aspect ratio: 3:4 (portrait poster) — suitable for print at 300 DPI.",
        "- Deliver a single striking image with clear typography and generous negative space.",
        "",
        "Design notes for image model:",
        "- Use low-saturation, warm tones for background and accent with one saturated accent color.",
        "- Keep text areas legible; prefer sans-serif, bold headline, medium body.",
        "",
        "Output should be a photorealistic / high-detail illustration suitable for a marketing poster. Do NOT include watermarks or visible model signatures."
    ]

    # 将 prompt_lines 合并为单个字符串
    return "\n".join([ln for ln in prompt_lines if ln.strip() != ""])

# --------------------
# 3) 调用图像模型（OpenRouter 示例）
# --------------------
def call_image_model(api_key, image_prompt_text, output_dir="output"):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "google/gemini-2.5-flash-image-preview",
        "messages": [
            {
                "role": "user",
                "content": image_prompt_text
            }
        ],
        # modalities 可能由模型/服务决定是否需要
        "modalities": ["image", "text"],
        "image_config": {
            "aspect_ratio": "2:3"
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()

    # 提取并保存生成的图片
    if result.get("choices"):
        message = result["choices"][0]["message"]
        if "images" in message:
            for i, image in enumerate(message["images"]):
                image_data_url = image["image_url"]["url"]

                # 如果是Base64编码格式，比如 data:image/png;base64,xxxxxx
                if image_data_url.startswith("data:image"):
                    header, encoded = image_data_url.split(",", 1)
                    image_bytes = base64.b64decode(encoded)

                    # 自动识别文件类型（png、jpeg等）
                    ext = header.split("/")[1].split(";")[0]
                    filename = f"{output_dir}/generated_image_{i}.{ext}"

                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                else:
                    # 如果返回的是真实URL（可下载链接）
                    img_data = requests.get(image_data_url).content
                    filename = f"generated_image_{i}.png"
                    with open(filename, "wb") as f:
                        f.write(img_data)

# --------------------
# 4) 完整调用示例（把上面三步串起来）
# --------------------
def generate_poster_pipeline(client, api_key, idea, output_dir):
    branding, raw = generate_branding(client, idea)
    image_prompt = build_image_prompt_from_branding(branding, fallback_raw_text=raw)
    print("=== Image Prompt ===\n", image_prompt[:2000].encode('utf-8', errors='replace').decode('utf-8'))
    call_image_model(api_key, image_prompt, output_dir)

def design(idea, output_dir="output", image_prompt=None):
    os.makedirs(output_dir, exist_ok=True)

    API_KEY_REF = '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'
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY_REF,
        )

    # 如果提供了image_prompt，直接使用它；否则使用原有的pipeline
    if image_prompt:
        print("=== Using provided image prompt ===\n", image_prompt[:2000].encode('utf-8', errors='replace').decode('utf-8'))
        call_image_model(API_KEY_REF, image_prompt, output_dir)
    else:
        generate_poster_pipeline(client, API_KEY_REF, idea, output_dir)
    # print("Image model response:", json.dumps(result, ensure_ascii=False, indent=2))
    
# --------------------
# 示例使用（替换 client, API_KEY_REF, idea）
# --------------------
if __name__ == "__main__":

    idea = "Chinese crepe - Freshly made street-food crepes with customizable savory and sweet fillings"
    output_dir = "output"
    design(idea, output_dir)
