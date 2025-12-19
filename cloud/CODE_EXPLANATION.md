# 📚 Code Explanation - Deep Dive into Each File

This document provides a detailed explanation of every file in the Hadoop MapReduce Word Counter project, how they work, and how they interact with each other.

---

## 📋 Table of Contents

1. [MapReduce Scripts](#mapreduce-scripts)
   - [mapper.py](#mapperpy)
   - [reducer.py](#reducerpy)
2. [Docker Configuration](#docker-configuration)
   - [docker-compose.yml](#docker-composeyml)
   - [hadoop.env](#hadoopenv)
3. [Backend API](#backend-api)
   - [app.py](#apppy)
4. [Frontend](#frontend)
   - [index.html](#indexhtml)

---

## 🔧 MapReduce Scripts

### mapper.py

**Location:** `mapreduce/mapper.py`

**Purpose:** Processes input text and emits word-count pairs for the Map phase of MapReduce.

**Complete Code:**
```python
#!/usr/bin/env python3
import sys
import re

def mapper(text):
    """Mapper function with text preprocessing"""
    word_count = []
    # Expand contractions

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
        # Apply mapper function to the line
        mapped_results = mapper(line)
        # Output in Hadoop format: word\t1
        for word, count in mapped_results:
            print("{}\t{}".format(word, count))
```

**Line-by-Line Breakdown:**

```python
#!/usr/bin/env python3
```
- **Shebang line**: Tells the system to use Python 3 to execute this script
- Required for Hadoop Streaming to recognize this as a Python script

```python
import sys
import re
```
- `sys`: Provides access to stdin/stdout for reading input and writing output
- `re`: Regular expression module for text pattern matching and replacement

```python
def mapper(text):
    """Mapper function with text preprocessing"""
    word_count = []
```
- Defines the mapper function that processes one line of text
- `word_count`: Will store tuples of (word, count) pairs
- **Note:** This is a helper function; the actual Hadoop input comes from stdin below

```python
    text = text.lower()
```
- Converts all text to lowercase
- **Why?** So "Hello" and "hello" are counted as the same word
- Example: "Hello World" → "hello world"

```python
    text = re.sub(r"[^\w\s]", " ", text)
```
- Removes all punctuation marks and special characters
- **Breakdown:**
  - `r"[^\w\s]"`: Regular expression pattern
    - `^`: NOT operator
    - `\w`: Word characters (letters, digits, underscore)
    - `\s`: Whitespace characters
    - `[^\w\s]`: Any character that's NOT a letter, digit, or space
  - `" "`: Replace matches with a space
- **Example:** "hello, world!" → "hello  world "

```python
    words = text.split()
```
- Splits text into individual words using whitespace as delimiter
- `.split()` with no argument splits on any whitespace and removes empty strings
- **Example:** "hello  world " → ["hello", "world"]

```python
    for word in words:
        if word:
            word_count.append((word, 1))
```
- Iterates through each word
- `if word:` checks that word is not empty
- Creates a tuple `(word, 1)` for each word
  - The `1` represents "this word occurred once"
- **Example:** ["hello", "world"] → [("hello", 1), ("world", 1)]

```python
    return word_count
```
- Returns the list of (word, count) tuples

```python
for line in sys.stdin:
```
- **THE ACTUAL HADOOP INPUT LOOP**
- Hadoop Streaming feeds input to this script via stdin
- Each line of the input file is read one at a time
- This is where Hadoop calls our script

```python
    line = line.strip()
```
- Removes leading/trailing whitespace from the line
- **Why?** Clean data, prevent empty lines from causing issues

```python
    if line:
        mapped_results = mapper(line)
```
- Only process non-empty lines
- Calls our mapper function on the line

```python
        for word, count in mapped_results:
            print("{}\t{}".format(word, count))
```
- **CRITICAL OUTPUT FORMAT**
- Hadoop Streaming expects output in format: `key\tvalue`
- `\t` is a TAB character (required by Hadoop)
- `{}` placeholders are filled by `.format()`
- **Example output:**
  ```
  hello	1
  world	1
  hello	1
  ```

**How Hadoop Uses This:**

1. Hadoop reads input file line by line
2. Sends each line to mapper via stdin
3. Mapper outputs: `word\t1` for each word
4. Hadoop collects all outputs
5. **Hadoop sorts and groups** all outputs by key (the word)
6. Sends sorted groups to reducer

**Example Execution:**

Input line:
```
Hello, World! Hello Hadoop.
```

Processing:
1. Lowercase: `hello, world! hello hadoop.`
2. Remove punctuation: `hello  world  hello hadoop `
3. Split: `["hello", "world", "hello", "hadoop"]`
4. Output:
   ```
   hello	1
   world	1
   hello	1
   hadoop	1
   ```

---

### reducer.py

**Location:** `mapreduce/reducer.py`

**Purpose:** Aggregates the word counts from the mapper output.

**Complete Code:**
```python
#!/usr/bin/env python3
import sys

def reducer(word_count_list):
    """Reducer function to aggregate word counts"""
    counts = {}
    for word, count in word_count_list:
        counts[word] = counts.get(word, 0) + count
    return counts

# For Hadoop Streaming, we need to process sorted input
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

**Line-by-Line Breakdown:**

```python
#!/usr/bin/env python3
import sys
```
- Same as mapper: shebang for Python 3 and sys for stdin/stdout

```python
def reducer(word_count_list):
    """Reducer function to aggregate word counts"""
    counts = {}
    for word, count in word_count_list:
        counts[word] = counts.get(word, 0) + count
    return counts
```
- **Note:** This function is NOT actually used in Hadoop Streaming
- It's a helper function that demonstrates the reduce logic
- The actual reduction happens in the loop below

```python
current_word = None
current_count = 0
```
- **State variables** to track the current word being processed
- `current_word`: The word we're currently counting
- `current_count`: Running total for the current word

**Why these variables?**
- Hadoop sends us **sorted** input, grouped by word
- Example input:
  ```
  apple	1
  apple	1
  apple	1
  banana	1
  banana	1
  ```
- We can process this efficiently by tracking the current word

```python
for line in sys.stdin:
    line = line.strip()
```
- Read input from Hadoop line by line
- Each line is output from a mapper: `word\t1`

```python
    try:
        word, count = line.split('\t')
        count = int(count)
    except:
        continue
```
- Parse the input line
- `line.split('\t')`: Split on TAB character into [word, count]
- `int(count)`: Convert count string to integer
- `try/except`: Skip malformed lines (defensive programming)

**Example:**
```
Input line: "hello\t1"
After split: word="hello", count=1
```

```python
    if word == current_word:
        current_count += count
```
- **Same word as before?** Add to running count
- This happens when Hadoop sends multiple occurrences of the same word
- Example:
  ```
  Current: word="hello", count=2
  New line: "hello\t1"
  Result: count=3
  ```

```python
    else:
        if current_word is not None:
            print("{}\t{}".format(current_word, current_count))
```
- **Different word?** We've finished counting the previous word
- Output the previous word and its total count
- `if current_word is not None`: Skip on first iteration (no previous word yet)

**Example:**
```
Current: word="hello", count=3
New line: "world\t1"
Output: "hello\t3"
Then: current_word="world", current_count=1
```

```python
        current_word = word
        current_count = count
```
- Start tracking the new word
- Initialize count with the count from this line

```python
if current_word is not None:
    print("{}\t{}".format(current_word, current_count))
```
- **Output the last word** after the loop ends
- **Why needed?** The loop ends after reading all input, but we haven't output the final word yet

**How Hadoop Uses This:**

1. Hadoop **sorts** all mapper outputs by key (word)
2. Groups: `hadoop → [1], hello → [1,1], world → [1]`
3. Sends sorted stream to reducer via stdin
4. Reducer aggregates and outputs final counts
5. Hadoop writes output to HDFS

**Complete Example:**

Mapper outputs (unsorted):
```
hello	1
world	1
hello	1
hadoop	1
```

After Hadoop sorts (input to reducer):
```
hadoop	1
hello	1
hello	1
world	1
```

Reducer processing:
1. Read `hadoop	1` → current_word="hadoop", current_count=1
2. Read `hello	1` → Different word! Output `hadoop	1`, set current_word="hello", current_count=1
3. Read `hello	1` → Same word! current_count=2
4. Read `world	1` → Different word! Output `hello	2`, set current_word="world", current_count=1
5. End of input → Output `world	1`

Final output:
```
hadoop	1
hello	2
world	1
```

---

## 🐳 Docker Configuration

### docker-compose.yml

**Location:** `docker-compose.yml`

**Purpose:** Defines and orchestrates the 4-node Hadoop cluster using Docker containers.

**Complete Code:**
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

**Section-by-Section Breakdown:**

```yaml
version: "3"
```
- Docker Compose file format version
- Version 3 is widely compatible and supports all features we need

```yaml
services:
```
- Defines all containers that will run
- Each service becomes a separate Docker container

---

#### NameNode Service

```yaml
  namenode:
    image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
```
- **Service name:** `namenode` (used for DNS within Docker network)
- **Image:** Pre-built Hadoop NameNode from Big Data Europe
  - `2.0.0`: Image version
  - `hadoop3.2.1`: Hadoop version
  - `java8`: Java version

```yaml
    container_name: namenode
```
- Name of the actual container (used in `docker exec namenode ...`)
- **Why important?** Allows us to run commands like `docker exec namenode hdfs dfs -ls /`

```yaml
    restart: always
```
- **Restart policy:** Always restart if container stops
- Ensures cluster stays running even after crashes or Docker restarts

```yaml
    ports:
      - 9870:9870
      - 9000:9000
```
- **Port mappings:** `host_port:container_port`
- `9870`: NameNode Web UI (browse HDFS, check cluster health)
  - Access at: http://localhost:9870
- `9000`: HDFS file system access port
  - Used by clients to read/write files

```yaml
    volumes:
      - hadoop_namenode:/hadoop/dfs/name
      - ./mapreduce:/opt/mapreduce
```
- **Volume 1:** `hadoop_namenode:/hadoop/dfs/name`
  - Named volume for persistent storage
  - Stores HDFS metadata (file locations, block info)
  - **Persists data** even when container is deleted
- **Volume 2:** `./mapreduce:/opt/mapreduce`
  - **Bind mount:** Maps local folder to container folder
  - Changes to `./mapreduce` on your computer appear in `/opt/mapreduce` in container
  - **Why?** So we can edit mapper.py/reducer.py locally and container sees changes

```yaml
    environment:
      - CLUSTER_NAME=test
```
- Sets environment variable inside container
- `CLUSTER_NAME`: Identifies this Hadoop cluster

```yaml
    env_file:
      - ./hadoop.env
```
- Loads ALL environment variables from `hadoop.env` file
- Contains dozens of Hadoop configuration settings

---

#### DataNode Service

```yaml
  datanode:
    image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
    container_name: datanode
    restart: always
```
- Similar structure to NameNode

```yaml
    volumes:
      - hadoop_datanode:/hadoop/dfs/data
```
- **Named volume** for storing actual HDFS data blocks
- This is where your files are physically stored

```yaml
    environment:
      SERVICE_PRECONDITION: "namenode:9870"
```
- **Wait condition:** Don't start until NameNode is ready
- Checks that `namenode:9870` is accessible
- **Why?** DataNode needs NameNode to be running first

---

#### ResourceManager Service

```yaml
  resourcemanager:
    image: bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8
    container_name: resourcemanager
    restart: always
    environment:
      SERVICE_PRECONDITION: "namenode:9000 namenode:9870 datanode:9864"
```
- **YARN ResourceManager:** Manages cluster resources
- **Precondition:** Wait for NameNode AND DataNode
- **Why multiple checks?** Needs both HDFS ports (9000, 9870) and DataNode (9864)

---

#### NodeManager Service

```yaml
  nodemanager:
    image: bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8
    container_name: nodemanager
    restart: always
    environment:
      SERVICE_PRECONDITION: "namenode:9000 namenode:9870 datanode:9864 resourcemanager:8088"
```
- **YARN NodeManager:** Actually runs MapReduce tasks
- **Precondition:** Wait for everything else
- **8088:** ResourceManager port

---

#### Volumes Definition

```yaml
volumes:
  hadoop_namenode:
  hadoop_datanode:
```
- **Declares named volumes** used by services
- Docker creates and manages these volumes
- Data persists across container restarts

**Why named volumes?**
- Persist data even when containers are removed
- Can be backed up with `docker volume` commands
- Better performance than bind mounts

---

### hadoop.env

**Location:** `hadoop.env`

**Purpose:** Configures Hadoop cluster settings via environment variables.

**Key Sections Explained:**

```env
CORE_CONF_fs_defaultFS=hdfs://namenode:9000
```
- **Default filesystem URI**
- All HDFS paths use this as root
- `hdfs://namenode:9000` means "contact namenode on port 9000 for file operations"

```env
HDFS_CONF_dfs_webhdfs_enabled=true
```
- Enables WebHDFS (REST API for HDFS)
- Allows HTTP access to HDFS

```env
HDFS_CONF_dfs_permissions_enabled=false
```
- **Disables UNIX-style permissions** in HDFS
- **Why?** Simplifies development (no permission errors)
- **Production:** Should be `true` for security

```env
HDFS_CONF_dfs_replication=1
```
- **Replication factor:** How many copies of each block
- `1` = Single copy (sufficient for development)
- **Production:** Use `3` for fault tolerance

```env
YARN_CONF_yarn_timeline___service_enabled=false
```
- **Timeline Service:** Tracks historical job data
- Disabled because it requires additional infrastructure (historyserver)
- **Why disabled?** Simplifies cluster setup

```env
MAPRED_CONF_mapreduce_framework_name=yarn
```
- **MapReduce framework:** Use YARN (vs older framework)
- **YARN** = Yet Another Resource Negotiator

```env
MAPRED_CONF_yarn_app_mapreduce_am_env=HADOOP_MAPRED_HOME=/opt/hadoop-3.2.1/
```
- Tells MapReduce where Hadoop is installed
- Required for finding JAR files and libraries

**How Environment Variables Become Hadoop Config:**

The Docker images automatically convert environment variables to Hadoop XML config files.

Example:
```env
CORE_CONF_fs_defaultFS=hdfs://namenode:9000
```

Becomes in `core-site.xml`:
```xml
<property>
  <name>fs.defaultFS</name>
  <value>hdfs://namenode:9000</value>
</property>
```

**Naming Convention:**
- `{COMPONENT}_CONF_{property}={value}`
- `COMPONENT`: CORE, HDFS, YARN, MAPRED
- `property`: Hadoop property name with `.` replaced by `_`

---

## 🖥️ Backend API

### app.py

**Location:** `backend/app.py`

**Purpose:** REST API that orchestrates Hadoop jobs via Docker CLI.

**Import Section:**

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import uuid
import os
```

- `FastAPI`: Modern web framework for building APIs
- `HTTPException`: For returning HTTP error responses
- `CORSMiddleware`: Allows frontend to call API from different domain
- `BaseModel`: For request/response validation
- `subprocess`: Run Docker commands from Python
- `uuid`: Generate unique job IDs
- `os`: File system operations

**App Initialization:**

```python
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- Creates FastAPI application
- **CORS**: Cross-Origin Resource Sharing
  - `allow_origins=["*"]`: Allow requests from ANY domain
  - **Why?** So frontend (file:///) can call API (http://localhost:8000)
  - **Production:** Should restrict to specific domains

**Configuration:**

```python
STREAMING_JAR = "/opt/hadoop-3.2.1/share/hadoop/tools/lib/hadoop-streaming-3.2.1.jar"
```
- Path to Hadoop Streaming JAR **inside the namenode container**
- Used to run MapReduce jobs

**Request Model:**

```python
class WordCountRequest(BaseModel):
    text: str
```
- Defines expected JSON structure for `/api/wordcount`
- FastAPI automatically validates requests
- Example valid request:
  ```json
  {
    "text": "hello world"
  }
  ```

---

**Status Endpoint:**

```python
@app.get('/api/status')
async def status():
    try:
        result = subprocess.run(
            ['docker', 'exec', 'namenode', 'hdfs', 'dfsadmin', '-report'],
            capture_output=True,
            text=True,
            timeout=10
        )
```

- **Decorator:** `@app.get('/api/status')` registers this as GET endpoint
- **async:** Allows concurrent request handling
- **Command:** Runs `hdfs dfsadmin -report` inside namenode container
  - Checks cluster health
  - Reports DataNode status
- **Parameters:**
  - `capture_output=True`: Capture stdout/stderr
  - `text=True`: Return output as string (not bytes)
  - `timeout=10`: Kill process after 10 seconds

```python
        if result.returncode == 0:
            return {'status': 'running', 'message': 'Cluster is healthy'}
        else:
            raise HTTPException(status_code=500, detail={'status': 'error', 'message': 'Cluster not responding', 'stderr': result.stderr})
    except Exception as e:
        raise HTTPException(status_code=500, detail={'status': 'error', 'message': str(e)})
```

- `returncode == 0`: Command succeeded
- Returns JSON response: `{"status": "running", ...}`
- **Error handling:** Returns 500 error if cluster is down

---

**WordCount Endpoint (Complete Flow):**

```python
@app.post('/api/wordcount')
async def wordcount(request: WordCountRequest):
    try:
        text = request.text
        if not text:
            raise HTTPException(status_code=400, detail={'error': 'No text provided'})
```
- **POST endpoint:** Accepts JSON body
- Validates request contains text

```python
        job_id = str(uuid.uuid4())[:8]
        input_file = f"input_{job_id}.txt"
        output_dir = f"output_{job_id}"
```
- Generates **unique job ID** (first 8 chars of UUID)
- Creates unique file names to avoid conflicts
- Example: `input_abc12345.txt`, `output_abc12345`

```python
        local_tmp = os.path.join(os.getcwd(), input_file)
        with open(local_tmp, 'w') as f:
            f.write(text)
```
- **Step 1:** Save input text to local file
- `os.getcwd()`: Current working directory
- `with open()`: Automatically closes file after writing

```python
        subprocess.run(['docker', 'cp', local_tmp, f'namenode:/tmp/{input_file}'], check=True)
```
- **Step 2:** Copy file from host to namenode container
- Command: `docker cp input_abc12345.txt namenode:/tmp/input_abc12345.txt`
- `check=True`: Raise exception if command fails

```python
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-mkdir', '-p', '/input'], check=True)
```
- **Step 3:** Create `/input` directory in HDFS
- `-p`: Create parent directories if needed (like `mkdir -p`)
- Command runs inside namenode container

```python
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-put', '-f', f'/tmp/{input_file}', '/input/'], check=True)
```
- **Step 4:** Upload file from container's /tmp to HDFS
- `-f`: Force overwrite if file exists
- Moves: `/tmp/input_abc12345.txt` → `hdfs:///input/input_abc12345.txt`

```python
        subprocess.run(['docker', 'exec', 'namenode', 'chmod', '+x', '/opt/mapreduce/mapper.py'], check=True)
        subprocess.run(['docker', 'exec', 'namenode', 'chmod', '+x', '/opt/mapreduce/reducer.py'], check=True)
```
- **Step 5:** Make Python scripts executable
- Required for Hadoop to run them
- `+x`: Add execute permission

```python
        subprocess.run([
            'docker', 'exec', 'namenode', 'hadoop', 'jar', STREAMING_JAR,
            '-files', '/opt/mapreduce/mapper.py,/opt/mapreduce/reducer.py',
            '-mapper', 'python3 mapper.py',
            '-reducer', 'python3 reducer.py',
            '-input', f'/input/{input_file}',
            '-output', f'/output/{output_dir}'
        ], check=True, capture_output=True, text=True)
```
- **Step 6:** Submit MapReduce job
- **Breaking down the command:**
  - `hadoop jar STREAMING_JAR`: Run Hadoop Streaming
  - `-files mapper.py,reducer.py`: Distribute these files to worker nodes
  - `-mapper "python3 mapper.py"`: Command to run for map phase
  - `-reducer "python3 reducer.py"`: Command to run for reduce phase
  - `-input /input/...`: Input file in HDFS
  - `-output /output/...`: Output directory in HDFS

**What happens during job execution:**
1. Hadoop reads input file from HDFS
2. Splits into chunks
3. Runs mapper on each chunk (in parallel)
4. Sorts mapper output
5. Runs reducer on sorted data
6. Writes results to HDFS

```python
        result = subprocess.run([
            'docker', 'exec', 'namenode', 'hdfs', 'dfs', '-cat', f'/output/{output_dir}/part-00000'
        ], capture_output=True, text=True, check=True)
```
- **Step 7:** Read job results from HDFS
- `part-00000`: Default output file name from single reducer
- `capture_output`: Get output as string

```python
        word_counts = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) == 2:
                    word, count = parts
                    word_counts[word] = int(count)
```
- **Step 8:** Parse results
- Input format: `word\tcount` (one per line)
- Creates dictionary: `{"hello": 2, "world": 1}`

```python
        total_words = sum(word_counts.values())
        unique_words = len(word_counts)
```
- Calculate statistics
- `sum(values())`: Total occurrences of all words
- `len()`: Number of unique words

```python
        os.remove(local_tmp)
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-rm', '-r', f'/input/{input_file}'])
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-rm', '-r', f'/output/{output_dir}'])
```
- **Step 9:** Cleanup
- Remove local temp file
- Delete input/output from HDFS
- **Why?** Save storage space

```python
        return {
            'job_id': job_id,
            'word_counts': word_counts,
            'total_words': total_words,
            'unique_words': unique_words
        }
```
- Return JSON response with results

```python
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise HTTPException(status_code=500, detail={'error': f'Hadoop error: {error_msg}'})
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e)})
```
- **Error handling**
- `CalledProcessError`: Command failed (Docker or Hadoop)
- Returns detailed error to frontend

```python
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
```
- **Run server** when script is executed directly
- `0.0.0.0`: Listen on all network interfaces
- `port=8000`: HTTP port

---

## 🎨 Frontend

### index.html

**Location:** `frontend/index.html`

**Purpose:** Beautiful web interface for submitting jobs and viewing results.

**Key JavaScript Functions:**

```javascript
const BASE = "https://belt-tourism-mixed-mating.trycloudflare.com";
```
- **API Base URL**
- Change this to your Cloudflare tunnel URL or `http://localhost:8000` for local testing

```javascript
async function checkStatus() {
  const el = document.getElementById("status");
  el.innerText = "⏳ Checking...";
```
- Gets reference to status display element
- Shows loading message

```javascript
  try {
    const res = await fetch(`${BASE}/api/status`);
    const data = await res.json();
    el.innerText = JSON.stringify(data, null, 2);
```
- **Fetch API:** Makes HTTP GET request to `/api/status`
- `await`: Waits for response
- `.json()`: Parses JSON response
- `JSON.stringify(..., null, 2)`: Pretty-print with 2-space indent

```javascript
  } catch (e) {
    el.innerText = "❌ " + e;
  }
}
```
- Error handling: Display error message

---

```javascript
async function runWordCount() {
  const text = document.getElementById("text").value.trim();
  if (!text) return alert("Enter text first!");
```
- Gets text from textarea
- `.trim()`: Remove leading/trailing whitespace
- Validates user entered something

```javascript
  document.getElementById("table").innerHTML = "<p>Running Hadoop job...</p>";
```
- Shows loading message in results area

```javascript
  try {
    const res = await fetch(`${BASE}/api/wordcount`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
```
- **POST request** to `/api/wordcount`
- Sets `Content-Type` header for JSON
- Sends `{"text": "user input"}` as request body

```javascript
    const data = await res.json();

    document.getElementById("total-words").innerText = data.total_words;
    document.getElementById("unique-words").innerText = data.unique_words;
```
- Parse response
- Update statistics cards with totals

```javascript
    buildTable(data.word_counts);
```
- Call function to build results table

```javascript
  } catch (e) {
    document.getElementById("table").innerHTML = "<p>Error: " + e + "</p>";
  }
}
```
- Error handling

---

```javascript
function buildTable(wordCounts) {
  if (!wordCounts || Object.keys(wordCounts).length === 0) return;
```
- Checks if there are results
- `Object.keys()`: Gets array of object keys

```javascript
  let html = `<table>
    <tr><th>Word</th><th>Count</th></tr>`;
  for (let w in wordCounts) {
    html += `<tr><td>${w}</td><td>${wordCounts[w]}</td></tr>`;
  }
  html += "</table>";
  document.getElementById("table").innerHTML = html;
}
```
- Builds HTML table dynamically
- `for...in`: Iterate over object keys
- Template literals: `` `${variable}` `` for string interpolation
- Sets innerHTML to inject table into page

**CSS Highlights:**

```css
body {
  background: #001f3f;
}
```
- Dark navy blue background

```css
.card {
  background: linear-gradient(145deg, #ffffff, #f8f9fa);
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
```
- Subtle gradient on cards
- Drop shadow for depth

```css
.card:hover {
  box-shadow: 0 15px 40px rgba(0,0,0,0.3);
}
```
- Enhanced shadow on hover

```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
```
- Smooth entrance animation
- Fades in while moving up

---

## 🔄 Complete Data Flow

1. **User enters text** in frontend
2. **Frontend sends POST** request with JSON
3. **Backend receives** request, validates
4. **Backend saves** text to local file
5. **Backend copies** file to namenode container
6. **Backend uploads** file to HDFS
7. **Backend submits** Hadoop job
8. **Hadoop splits** input across mappers
9. **Mappers process** chunks in parallel → word counts
10. **Hadoop sorts** mapper outputs by word
11. **Reducers aggregate** counts per word
12. **Hadoop writes** results to HDFS
13. **Backend reads** results from HDFS
14. **Backend parses** and formats results
15. **Backend returns** JSON to frontend
16. **Frontend displays** results in beautiful table

---

**End of Code Explanation Document**

*This document provides deep technical details on every component. Use it as a reference when modifying or extending the system.*
