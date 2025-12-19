# 🚀 Hadoop MapReduce Word Counter - Complete Setup Guide

A production-ready Hadoop MapReduce cluster with modern web interface for distributed word counting.

![Hadoop](https://img.shields.io/badge/Hadoop-3.2.1-orange) ![Python](https://img.shields.io/badge/Python-3.5+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green) ![Docker](https://img.shields.io/badge/Docker-Required-blue)

---

## 📋 Table of Contents

- [What is MapReduce?](#what-is-mapreduce)
- [System Architecture](#system-architecture)
- [Components](#components)
- [Installation from Scratch](#installation-from-scratch)
- [Running the Application](#running-the-application)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## 🤔 What is MapReduce?

MapReduce is a programming model for processing large datasets across distributed systems.

### How It Works:

**1. Map Phase:**
- Splits input into smaller chunks
- Processes each chunk in parallel
- Outputs key-value pairs

Example:
```
Input: "hello world hello hadoop"

Mapper Output:
hello → 1
world → 1
hello → 1
hadoop → 1
```

**2. Shuffle & Sort Phase (Automatic):**
- Groups all values by key
- Sorts keys alphabetically

```
hadoop → [1]
hello → [1, 1]
world → [1]
```

**3. Reduce Phase:**
- Aggregates values for each key
- Produces final output

```
hadoop → 1
hello → 2
world → 1
```

### Why Use MapReduce?

✅ **Scalability** - Process terabytes across thousands of machines
✅ **Fault Tolerance** - Automatically handles node failures
✅ **Parallel Processing** - Distributes workload efficiently
✅ **Abstraction** - Framework handles complexity

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────┐
│           User Interface (Web Browser)           │
│              Beautiful Dashboard                  │
└────────────────────┬─────────────────────────────┘
                     │ HTTPS Requests
                     ▼
┌──────────────────────────────────────────────────┐
│         FastAPI Backend (Python REST API)        │
│        Orchestrates Jobs via Docker CLI          │
└────────────────────┬─────────────────────────────┘
                     │ Docker Exec
                     ▼
┌──────────────────────────────────────────────────┐
│           Hadoop Cluster (4 Containers)          │
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐     │
│  │NameNode │  │DataNode │  │ResourceMgr  │     │
│  │(Master) │  │(Storage)│  │   (YARN)    │     │
│  └─────────┘  └─────────┘  └─────────────┘     │
│                 ┌─────────────┐                  │
│                 │NodeManager  │                  │
│                 │  (Worker)   │                  │
│                 └─────────────┘                  │
└──────────────────────────────────────────────────┘
```

---

## 🧩 Components

### 1. Hadoop Cluster (4 Docker Containers)

#### **NameNode** - Master Node
- **Image:** `bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8`
- **Role:** Manages file system metadata
- **Tasks:**
  - Maintains directory structure
  - Tracks file block locations
  - Handles client requests
- **Ports:** 9870 (Web UI), 9000 (HDFS)

#### **DataNode** - Storage Node
- **Image:** `bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8`
- **Role:** Stores actual data blocks
- **Tasks:**
  - Stores and retrieves blocks
  - Reports to NameNode
  - Handles replication

#### **ResourceManager** - YARN Master
- **Image:** `bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8`
- **Role:** Manages cluster resources
- **Tasks:**
  - Allocates resources
  - Schedules jobs
  - Monitors execution

#### **NodeManager** - YARN Worker
- **Image:** `bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8`
- **Role:** Executes tasks
- **Tasks:**
  - Runs MapReduce containers
  - Monitors resource usage
  - Reports to ResourceManager

### 2. Backend API (FastAPI)
- REST API endpoints
- Job submission
- Result parsing
- Docker orchestration

### 3. Frontend (HTML/CSS/JS)
- Beautiful web interface
- Real-time job status
- Interactive results table
- Statistics display

### 4. MapReduce Scripts

**Mapper (mapper.py):**
- Reads text line by line
- Splits into words
- Outputs: `word\t1`

**Reducer (reducer.py):**
- Receives sorted word-count pairs
- Aggregates counts per word
- Outputs: `word\ttotal_count`

---

## 📦 Installation from Scratch

### Step 1: Install Python

**Windows:**
1. Download: https://www.python.org/downloads/
2. Run installer
3. ✅ **CHECK:** "Add Python to PATH"
4. Verify:
   ```powershell
   python --version
   ```

**macOS:**
```bash
brew install python3
```

**Linux:**
```bash
sudo apt update && sudo apt install python3 python3-pip
```

---

### Step 2: Install Docker Desktop

1. Download: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Verify:
   ```bash
   docker --version
   docker-compose --version
   ```

---

### Step 3: Create Project Structure

```bash
mkdir hadoop-wordcount
cd hadoop-wordcount
```

Create these folders:
```
hadoop-wordcount/
├── backend/
├── frontend/
└── mapreduce/
```

---

### Step 4: Create MapReduce Scripts

**Create `mapreduce/mapper.py`:**
```python
#!/usr/bin/env python3
import sys
import re

def mapper(text):
    """Mapper function with text preprocessing"""
    word_count = []
    # Lowercase and remove punctuation
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = text.split()
    for word in words:
        if word:
            word_count.append((word, 1))
    return word_count

# Read from stdin and apply mapper
for line in sys.stdin:
    line = line.strip()
    if line:
        mapped_results = mapper(line)
        for word, count in mapped_results:
            print("{}\t{}".format(word, count))
```

**Create `mapreduce/reducer.py`:**
```python
#!/usr/bin/env python3
import sys

current_word = None
current_count = 0

for line in sys.stdin:
    line = line.strip()
    try:
        word, count = line.split('\t')
        count = int(count)
    except:
        continue

    if word == current_word:
        current_count += count
    else:
        if current_word is not None:
            print("{}\t{}".format(current_word, current_count))
        current_word = word
        current_count = count

if current_word is not None:
    print("{}\t{}".format(current_word, current_count))
```

---

### Step 5: Create Docker Configuration

**Create `docker-compose.yml`:**
```yaml
version: "3"

services:
  namenode:
    image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
    container_name: namenode
    restart: always
    ports:
      - 9870:9870
      - 9000:9000
    volumes:
      - hadoop_namenode:/hadoop/dfs/name
      - ./mapreduce:/opt/mapreduce
    environment:
      - CLUSTER_NAME=test
    env_file:
      - ./hadoop.env

  datanode:
    image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
    container_name: datanode
    restart: always
    volumes:
      - hadoop_datanode:/hadoop/dfs/data
    environment:
      SERVICE_PRECONDITION: "namenode:9870"
    env_file:
      - ./hadoop.env

  resourcemanager:
    image: bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8
    container_name: resourcemanager
    restart: always
    environment:
      SERVICE_PRECONDITION: "namenode:9000 namenode:9870 datanode:9864"
    env_file:
      - ./hadoop.env

  nodemanager:
    image: bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8
    container_name: nodemanager
    restart: always
    environment:
      SERVICE_PRECONDITION: "namenode:9000 namenode:9870 datanode:9864 resourcemanager:8088"
    env_file:
      - ./hadoop.env

volumes:
  hadoop_namenode:
  hadoop_datanode:
```

**Create `hadoop.env`:**
```env
CORE_CONF_fs_defaultFS=hdfs://namenode:9000
CORE_CONF_hadoop_http_staticuser_user=root

HDFS_CONF_dfs_webhdfs_enabled=true
HDFS_CONF_dfs_permissions_enabled=false
HDFS_CONF_dfs_replication=1

YARN_CONF_yarn_log_aggregation_enable=false
YARN_CONF_yarn_resourcemanager_hostname=resourcemanager
YARN_CONF_yarn_resourcemanager_address=resourcemanager:8032
YARN_CONF_yarn_timeline___service_enabled=false
YARN_CONF_yarn_nodemanager_aux___services=mapreduce_shuffle

MAPRED_CONF_mapreduce_framework_name=yarn
MAPRED_CONF_yarn_app_mapreduce_am_env=HADOOP_MAPRED_HOME=/opt/hadoop-3.2.1/
MAPRED_CONF_mapreduce_map_env=HADOOP_MAPRED_HOME=/opt/hadoop-3.2.1/
MAPRED_CONF_mapreduce_reduce_env=HADOOP_MAPRED_HOME=/opt/hadoop-3.2.1/
```

---

### Step 6: Create Backend API

**Install dependencies:**
```bash
pip install fastapi uvicorn pydantic
```

**Create `backend/app.py`:**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STREAMING_JAR = "/opt/hadoop-3.2.1/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar"

class WordCountRequest(BaseModel):
    text: str

@app.get('/api/status')
async def status():
    try:
        result = subprocess.run(
            ['docker', 'exec', 'namenode', 'hdfs', 'dfsadmin', '-report'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return {'status': 'running', 'message': 'Cluster is healthy'}
        else:
            raise HTTPException(status_code=500, detail={'status': 'error'})
    except Exception as e:
        raise HTTPException(status_code=500, detail={'status': 'error', 'message': str(e)})

@app.post('/api/wordcount')
async def wordcount(request: WordCountRequest):
    try:
        text = request.text
        if not text:
            raise HTTPException(status_code=400, detail={'error': 'No text provided'})

        job_id = str(uuid.uuid4())[:8]
        input_file = f"input_{job_id}.txt"
        output_dir = f"output_{job_id}"

        # Save input locally
        local_tmp = os.path.join(os.getcwd(), input_file)
        with open(local_tmp, 'w') as f:
            f.write(text)

        # Copy to container
        subprocess.run(['docker', 'cp', local_tmp, f'namenode:/tmp/{input_file}'], check=True)

        # Upload to HDFS
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-mkdir', '-p', '/input'], check=True)
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-put', '-f', f'/tmp/{input_file}', '/input/'], check=True)

        # Make scripts executable
        subprocess.run(['docker', 'exec', 'namenode', 'chmod', '+x', '/opt/mapreduce/mapper.py'], check=True)
        subprocess.run(['docker', 'exec', 'namenode', 'chmod', '+x', '/opt/mapreduce/reducer.py'], check=True)

        # Run Hadoop job
        subprocess.run([
            'docker', 'exec', 'namenode', 'hadoop', 'jar', STREAMING_JAR,
            '-files', '/opt/mapreduce/mapper.py,/opt/mapreduce/reducer.py',
            '-mapper', 'python3 mapper.py',
            '-reducer', 'python3 reducer.py',
            '-input', f'/input/{input_file}',
            '-output', f'/output/{output_dir}'
        ], check=True, capture_output=True, text=True)

        # Read output
        result = subprocess.run([
            'docker', 'exec', 'namenode', 'hdfs', 'dfs', '-cat', f'/output/{output_dir}/part-00000'
        ], capture_output=True, text=True, check=True)

        word_counts = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) == 2:
                    word, count = parts
                    word_counts[word] = int(count)

        total_words = sum(word_counts.values())
        unique_words = len(word_counts)

        # Cleanup
        os.remove(local_tmp)
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-rm', '-r', f'/input/{input_file}'])
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-rm', '-r', f'/output/{output_dir}'])

        return {
            'job_id': job_id,
            'word_counts': word_counts,
            'total_words': total_words,
            'unique_words': unique_words
        }

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise HTTPException(status_code=500, detail={'error': f'Hadoop error: {error_msg}'})
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e)})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
```

---

### Step 7: Create Frontend

**Create `frontend/index.html`:** (Use the beautiful HTML file you already have)

---

### Step 8: Start Hadoop Cluster

```bash
# Start containers
docker-compose up -d

# Wait 60 seconds
sleep 60

# Check cluster health
docker exec namenode hdfs dfsadmin -report
```

You should see: `Live datanodes (1)`

---

### Step 9: Install Python3 on Worker Nodes

```bash
# Install on NodeManager
docker exec nodemanager bash -c "echo 'deb http://archive.debian.org/debian stretch main' > /etc/apt/sources.list && apt-get update && apt-get install -y python3"

# Install on DataNode
docker exec datanode bash -c "echo 'deb http://archive.debian.org/debian stretch main' > /etc/apt/sources.list && apt-get update && apt-get install -y python3"

# Verify
docker exec nodemanager python3 --version
docker exec datanode python3 --version
```

---

## 🚀 Running the Application

### Start Backend:
```bash
cd backend
python app.py
```
Backend runs on: http://localhost:8000

### Open Frontend:
Simply open `frontend/index.html` in your browser.

---

## 🌐 Deployment

### Expose API Publicly (Cloudflare Tunnel):

1. Download cloudflared:
   - https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe

2. Run tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

3. You'll get a public URL like:
   ```
   https://random-words.trycloudflare.com
   ```

4. Update frontend `index.html` line 243:
   ```javascript
   const BASE = "https://your-tunnel-url.trycloudflare.com";
   ```

### Deploy Frontend (Netlify):

1. Go to: https://app.netlify.com/drop
2. Drag `frontend` folder
3. Done! Get instant public URL

---

## 🐛 Troubleshooting

### DataNode not connecting:
```bash
docker-compose down -v
docker-compose up -d
sleep 60
docker exec namenode hdfs dfsadmin -report
```

### Python3 not found:
```bash
docker exec nodemanager bash -c "echo 'deb http://archive.debian.org/debian stretch main' > /etc/apt/sources.list && apt-get update && apt-get install -y python3"
```

### Output directory exists:
```bash
docker exec namenode hdfs dfs -rm -r /output/*
```

---

## 📊 Useful Commands

```bash
# List HDFS files
docker exec namenode hdfs dfs -ls /

# View file
docker exec namenode hdfs dfs -cat /path/to/file

# Check cluster
docker exec namenode hdfs dfsadmin -report

# Monitor containers
docker stats

# View logs
docker logs namenode
```

---

## 🎯 Quick Start Summary

```bash
# 1. Install Python + Docker

# 2. Start Hadoop
docker-compose up -d

# 3. Install Python3 on workers
docker exec nodemanager bash -c "echo 'deb http://archive.debian.org/debian stretch main' > /etc/apt/sources.list && apt-get update && apt-get install -y python3"
docker exec datanode bash -c "echo 'deb http://archive.debian.org/debian stretch main' > /etc/apt/sources.list && apt-get update && apt-get install -y python3"

# 4. Install backend deps
pip install fastapi uvicorn pydantic

# 5. Start backend
cd backend && python app.py

# 6. Open frontend/index.html

# 7. Process big data! 🎉
```

---

**Built with ❤️ using Apache Hadoop, Docker, FastAPI, and modern web tech.**

*Last updated: December 2025*
