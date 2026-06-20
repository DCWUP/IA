import torch
import os
from diffusers import CogVideoXPipeline
from diffusers.utils import export_to_video

# 模型路径
model_path = "E:/CogVideoX-2b"

print(f"检查模型路径: {model_path}")
print(f"路径存在: {os.path.exists(model_path)}")
if os.path.exists(model_path):
    print(f"目录内容: {os.listdir(model_path)}")

print(f"PyTorch: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")

# 简单测试提示词
test_prompt = "A panda playing guitar in bamboo forest, sunlight, peaceful atmosphere, high quality"

print("\n开始加载模型...")
try:
    pipe = CogVideoXPipeline.from_pretrained(
        model_path,
        torch_dtype=torch.float32  # CPU 用 float32
    )
    print("模型加载成功")

    pipe.to("cpu")
    print("模型已移至 CPU")

    # 生成测试视频（少帧、少步数，快速验证）
    print("开始生成测试视频...")
    video = pipe(
        prompt=test_prompt,
        num_videos_per_prompt=1,
        num_inference_steps=10,      # 极少步数快速验证
        num_frames=8,                # 极少帧数
        guidance_scale=6,
        generator=torch.Generator(device="cpu").manual_seed(42),
    ).frames[0]

    # 导出
    export_to_video(video, "test_output.mp4", fps=8)
    print("测试成功！视频已保存为 test_output.mp4")
    print(f"视频帧数: {len(video)}, 分辨率: {video[0].size}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
