from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import uuid
import os

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Updated Hadoop Streaming JAR path
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
            raise HTTPException(status_code=500, detail={'status': 'error', 'message': 'Cluster not responding', 'stderr': result.stderr})
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

        # Create HDFS input dir
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-mkdir', '-p', '/input'])

        # Put file into HDFS
        subprocess.run(['docker', 'exec', 'namenode', 'hdfs', 'dfs', '-put', '-f', f'/tmp/{input_file}', '/input/'], check=True)

        # Make mapper/reducer executable
        subprocess.run(['docker', 'exec', 'namenode', 'chmod', '+x', '/opt/mapreduce/mapper.py'])
        subprocess.run(['docker', 'exec', 'namenode', 'chmod', '+x', '/opt/mapreduce/reducer.py'])

        # Run Hadoop streaming job
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

        # Cleanup local and HDFS files
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
        error_msg = e.stderr if e.stderr else e.stdout if e.stdout else str(e)
        raise HTTPException(status_code=500, detail={'error': f'Hadoop error: {error_msg}', 'returncode': e.returncode})
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e), 'type': type(e).__name__})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
