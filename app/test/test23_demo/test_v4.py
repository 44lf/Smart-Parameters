from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import tiktoken  # 用于 token 计数


# 1. 初始化 Ollama 模型（使用新版本导入）
def get_num_tokens(text: str) -> int:
    """使用 tiktoken 计算 token 数量，避免 GPT2 tokenizer 错误"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


class CustomOllamaLLM(OllamaLLM):
    """自定义 OllamaLLM 类，修复 token 计数问题"""

    def get_num_tokens(self, text: str) -> int:
        return get_num_tokens(text)

    def get_num_tokens_from_messages(self, messages: list) -> int:
        return sum([get_num_tokens(str(message)) for message in messages])


# 2. 初始化模型
model_name = "qwen3:0.6b"  # 或您使用的其他模型
llm = CustomOllamaLLM(model=model_name)

# 3. 使用新的 OllamaEmbeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")


def advanced_summarization(long_text, model_name="qwen3:0.6b"):
    """修复后的摘要函数"""

    # 使用修复后的 LLM
    llm = CustomOllamaLLM(model=model_name)

    # 文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=get_num_tokens  # 使用自定义 token 计数
    )

    # 分割文本
    docs = text_splitter.create_documents([long_text])
    print(f"将文本分割为 {len(docs)} 个段落")

    # 创建摘要链 - 使用更兼容的配置
    chain = load_summarize_chain(
        llm=llm,
        chain_type="map_reduce",
        verbose=True,
        token_max=4000,  # 限制最大 token 数
    )

    # 生成摘要
    try:
        result = chain.invoke(docs)
        return result['output_text']
    except Exception as e:
        print(f"摘要生成错误: {e}")
        # 备用方案：直接使用 LLM 生成摘要
        return fallback_summarization(long_text, llm)


def fallback_summarization(text, llm):
    """备用摘要方案"""
    prompt = f"请为以下文本生成一个简洁的摘要：\n\n{text[:3000]}...\n\n摘要："
    return llm.invoke(prompt)


# 您的长文本
your_long_text = """
大模型量化是通过降低模型参数和激活值的精度（如从 FP32 转为 INT8/INT4）来减少存储需求、加速推理并降低能耗的核心技术。以下是其核心原理、技术细节及 2025 年最新进展的全面解析：
一、核心原理与量化方法
1. 基础概念
量化本质：将高精度浮点数（如 FP32）映射到低精度整数（如 INT8），通过缩放因子（Scale）和零点（Zero Point）实现线性映射。例如，FP32 的1.2345可量化为 INT8 的1或2，在精度损失可控的前提下压缩模型体积。
核心目标：在模型性能下降不超过 1% 的前提下，实现存储占用减少 2-10 倍、推理速度提升 1.5-3 倍。
2. 主流量化技术
训练后量化（PTQ）：无需重新训练，直接对权重进行量化。分为：
动态量化：仅量化权重，激活值在推理时动态计算，适用于 Transformer 等模型（如 PyTorch 的torch.quantization）。
静态量化：权重和激活值均提前量化，需校准数据统计分布（如 TensorRT 的IInt8MinMaxCalibrator）。
量化感知训练（QAT）：在训练中插入伪量化算子，模拟量化误差，适用于高精度需求场景（如医疗影像分析）。
量化感知微调（QAF）：在微调阶段引入量化，平衡压缩与性能（如 LoRA 与量化结合）。
3. 低比特量化技术
GPTQ：针对 Transformer 的逐层迭代量化，通过贪心算法最小化误差，在 4 位量化下仍保持较高精度（如 LLaMA-7B 量化后 PPL 仅上升 5%）。
AWQ/AutoAWQ：激活感知权重量化，通过分析激活值分布优化权重量化范围，4 位量化推理速度比 FP16 快 3 倍，内存占用减少 3 倍。
OSTQuant（ICLR 2025）：新一代后训练量化方法，在 W4A4KV4（权重 4 位、激活 4 位、KV 缓存 4 位）配置下保持 96% 的原始性能，推理加速 3.4 倍，显存占用降至 38.41GB。
二、工具链与框架支持
1. 主流框架
PyTorch：支持动态 / 静态量化，通过torch.quantization模块实现，可集成bitsandbytes库进行 8 位 / 4 位量化（如bnb.nn.Linear8bitLt）。
TensorRT：NVIDIA 推理优化器，支持 INT8/FP16 量化，提供熵校准器（IInt8EntropyCalibrator2）和最小 - 最大校准器（IInt8MinMaxCalibrator），适合 GPU 部署。
llama.cpp：开源 C++ 库，支持 GGUF 格式量化，提供多种量化类型（如 Q4_K_M、Q5_K_M），适合 CPU / 低功耗设备。
Hugging Face Transformers：通过AutoModelForCausalLM.from_pretrained直接加载量化模型，支持bitsandbytes和peft库进行混合精度训练。
2. 量化参数配置
GGUF 量化类型：
平衡方案：Q4_K_M（4 位，块大小 128）在 CPU 上推理速度快，精度损失较小。
极致优化：Q3_K_M（3 位）或 IQ2_XS（2 位）适合极低显存场景，但可能损失部分精度。
Ollama 配置：通过model参数指定量化模型（如qwen3:0.6b），支持动态加载不同量化版本。
三、硬件适配与性能优化
1. 硬件类型与量化策略
GPU（NVIDIA A100/H100）：优先使用 FP16/INT8 混合精度，利用 TensorRT 优化卷积层融合，减少访存开销。
CPU（Intel Xeon/AMD EPYC）：选择 Q4_K_M 或 Q5_K_M 量化，利用 AVX-512 指令集加速整数运算。
边缘设备（手机 / 车载终端）：采用 INT8/INT4 静态量化，结合 CoreML 或 NNAPI 框架实现本地实时推理。
2. 性能对比
量化类型	显存占用（LLaMA-7B）	推理速度（RTX 4090）	精度损失（PPL）
FP16	28GB	1 token/0.04s	0%
Q4_K_M	7GB	1 token/0.025s	3-5%
Q3_K_M	5.25GB	1 token/0.02s	8-12%
OSTQuant W4A4KV4	7GB	1 token/0.018s	4%
（数据来源：）
四、精度损失与解决方案
1. 误差来源
位宽限制：低精度整数无法精确表示原始浮点数，导致信息丢失。
激活值分布：非对称或重尾分布的激活值易超出量化范围，引发溢出误差。
2. 优化策略
异常值处理：通过校准数据统计激活值分布，剪裁尾部异常值（如 TensorRT 的熵校准器）。
混合精度量化：对敏感层（如注意力头）保留较高精度，其他层采用低精度（如bitsandbytes的Linear8bitLt）。
知识蒸馏：量化后模型通过蒸馏学习全精度模型的知识，补偿精度损失。
五、最新进展与未来趋势
1. 2025 年技术突破
OSTQuant：通过正交变换优化权重分布，在 W4A4KV4 配置下性能超越现有方法，为边缘设备部署千亿参数模型提供可能。
AutoAWQ 自动化：支持一键式 4 位量化，无需手动调参，兼容 LLaMA、Vicuna 等主流模型。
混合精度推理：框架原生支持 FP16/INT8 动态切换，根据输入复杂度自动调整精度，平衡速度与准确性。
2. 未来方向
动态量化增强：结合实时数据自适应调整量化参数，减少长尾数据场景的精度损失。
硬件协同设计：与 ASIC/FPGA 厂商合作，针对特定量化格式优化硬件架构（如 INT4 专用计算单元）。
跨框架兼容性：推动 ONNX 等中间格式对低比特量化的统一支持，降低部署门槛。
六、实战建议
工具选择：
快速验证：使用llama.cpp的 Q4_K_M 量化，在 CPU 上测试模型可用性。
高精度需求：采用bitsandbytes+QAT 进行 8 位量化训练。
极致优化：用 AutoAWQ 进行 4 位量化，搭配 TensorRT 部署到 GPU。
评估指标：
生成类模型：计算困惑度（PPL）、BLEU/ROUGE 分数。
推理速度：测量单 token 生成时间（ms/token）或吞吐量（tokens/s）。
显存占用：使用nvidia-smi监控模型加载后的 GPU 内存使用。
部署流程：
python
运行
# 示例：使用AutoAWQ进行4位量化
from autoawq import AutoAWQForCausalLM

model = AutoAWQForCausalLM.from_quantized(
    "lmsys/vicuna-7b-v1.5",
    quantize_config="w4a16_128g",  # 4位权重，16位激活，块大小128
    device_map="auto"
)
通过合理选择量化方法、工具链和硬件配置，开发者可在性能与资源之间找到最佳平衡点，推动大模型从云端向边缘设备的广泛落地。
"""

# 执行摘要
if __name__ == "__main__":
    summary = advanced_summarization(your_long_text)
    print("\n最终摘要:")
    print("-" * 50)
print(summary)