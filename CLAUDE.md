# CLAUDE.md

## 环境注意事项

- recall 项目使用 **conda 环境 `recall`**，不要使用 uv/pip 直接安装依赖，应使用 `conda run -n recall pip install ...` 或先 `conda activate recall`
- 运行 recall 服务前必须 `conda activate recall`，否则会因为找不到已安装的包（如 rapidocr-onnxruntime）而降级或报错
