from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "Flask backend is running."

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/generate-image", methods=["POST"])
def generate_image():
    data = request.get_json() or {}

    mode = data.get("mode", "分割型")
    sides = data.get("sides", "8")
    layers = data.get("layers", "2")
    fold_count = data.get("foldCount", "12")
    opening = data.get("opening", "1.0")
    height = data.get("height", "48")
    tilt = data.get("tilt", "24")
    thickness = data.get("thickness", "2")
    radius = data.get("radius", "180")

    ark_api_key = os.environ.get("ARK_API_KEY")
    print("ARK_API_KEY loaded:", bool(ark_api_key))

    if not ark_api_key:
        return jsonify({"error": "未配置 ARK_API_KEY"}), 500

    prompt = f"""
请生成一张高端产品效果图，主体是一款参数化金属折面果盘。

要求：
1. 产品风格高端、极简、艺术化、电商海报级别；
2. 材质为镜面不锈钢 / 银灰金属；
3. 产品具有锋利折面、参数化切割、低多边形结构感；
4. 画面干净，白色或浅灰背景，专业棚拍光，强高光反射；
5. 视角为 3/4 产品视角，清晰展示整体结构；
6. 产品要真实、精致、可制造，不要像草图；
7. 强调金属 CMF 质感、镜面反射和高级感。

当前参数：
- 造型方式：{mode}
- 多边形边数：{sides}
- 层级数量：{layers}
- 折面数量：{fold_count}
- 开口比例：{opening}
- 整体高度：{height} mm
- 壁板倾角：{tilt}°
- 金属板厚度：{thickness} mm
- 整体半径：{radius} mm
"""

    url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ark_api_key}"
    }

    payload = {
        "model": "doubao-seedream-4-0-250828",
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": "2K",
        "stream": False,
        "watermark": True
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        print("Ark status:", response.status_code)
        print("Ark response:", response.text[:1000])

        if response.status_code != 200:
            return jsonify({
                "error": f"火山接口请求失败，状态码：{response.status_code}",
                "detail": response.text
            }), 500

        result = response.json()

        # 常见返回格式兼容
        if "data" in result and isinstance(result["data"], list) and len(result["data"]) > 0:
            first_item = result["data"][0]
            if isinstance(first_item, dict):
                if first_item.get("url"):
                    return jsonify({"image": first_item["url"]})
                if first_item.get("image_url"):
                    return jsonify({"image": first_item["image_url"]})

        if result.get("url"):
            return jsonify({"image": result["url"]})

        if result.get("image_url"):
            return jsonify({"image": result["image_url"]})

        return jsonify({
            "error": "接口返回成功，但没找到图片地址",
            "raw_result": result
        }), 500

    except Exception as e:
        print("Ark error:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)