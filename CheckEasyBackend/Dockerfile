# File: CheckEasyBackend/Dockerfile
FROM condaforge/mambaforge:latest

WORKDIR /app

# 将 Conda 环境配置文件和 .condarc 复制到容器中
COPY environment.yml .
COPY .condarc /opt/conda/.condarc

# 使用循环重试 apt-get update，增加 --fix-missing 以应对网络问题
RUN for i in 1 2 3 4 5; do \
      apt-get update --fix-missing && break || (echo "apt-get update failed, retrying ($i)..." && sleep 5); \
    done && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libblas-dev \
      liblapack-dev \
      libblis-dev \
      ca-certificates --fix-missing && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 设置环境变量，禁用 BLIS 的特定硬件优化并使用通用架构
ENV BLIS_DISABLE_AVX2=1
ENV BLIS_ARCH=generic
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# 使用 mamba 创建 Conda 环境，并清理缓存
RUN mamba env create -f environment.yml && conda clean -afy

# 激活新创建的 Conda 环境
ENV PATH /opt/conda/envs/myenv/bin:$PATH

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]