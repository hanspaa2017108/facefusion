# import os
# import tempfile
# import subprocess
# import time
# import shutil
# import requests
# from pathlib import Path as PathLib
# from tqdm import tqdm
# from cog import BasePredictor, Path, Input

# class Predictor(BasePredictor):
#     def setup(self):
#         """Download models, verify, and prepare environment."""
#         # Use .assets/models as the canonical location for models
#         self.model_dir = ".assets/models"
#         os.makedirs(self.model_dir, exist_ok=True)
        
#         # Model file URLs
#         model_files = {
#             "xseg_1.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.1.0/xseg_1.onnx",
#             "bisenet_resnet_34.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/bisenet_resnet_34.onnx",
#             "GFPGANv1.4.pth": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
#             "inswapper_128.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/inswapper_128.onnx",
#             "2dfan4.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/2dfan4.onnx",
#             "yoloface_8n.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/yoloface_8n.onnx"
#         }
        
#         # Model descriptions for reporting
#         model_descriptions = {
#             "yoloface_8n.onnx": "Face Detector",
#             "2dfan4.onnx": "Face Landmarker",
#             "inswapper_128.onnx": "Face Swapper",
#             "GFPGANv1.4.pth": "Face Enhancer",
#             "xseg_1.onnx": "Face Occluder",
#             "bisenet_resnet_34.onnx": "Face Parser"
#         }
        
#         # Download models
#         for model_file, url in model_files.items():
#             model_path = os.path.join(self.model_dir, model_file)
            
#             # Skip if model already exists
#             if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
#                 print(f"Model {model_file} already exists")
#                 continue
            
#             print(f"Downloading {model_file} from {url}...")
            
#             try:
#                 # Stream download with progress reporting
#                 response = requests.get(url, stream=True)
#                 response.raise_for_status()
                
#                 # Get content length if available
#                 total_size = int(response.headers.get('content-length', 0))
                
#                 # Download with progress bar
#                 with tempfile.NamedTemporaryFile(delete=False) as temp_file:
#                     with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
#                         for chunk in response.iter_content(chunk_size=8192):
#                             if chunk:
#                                 temp_file.write(chunk)
#                                 pbar.update(len(chunk))
#                     temp_path = temp_file.name
                
#                 # Move to final location
#                 shutil.move(temp_path, model_path)
#                 print(f"Successfully downloaded {model_file}")
#             except Exception as e:
#                 print(f"Error downloading {model_file}: {str(e)}")
#                 if os.path.exists(model_path) and os.path.getsize(model_path) == 0:
#                     os.remove(model_path)  # Remove empty file if download failed
        
#         # Set environment variables - point to .assets/models
#         os.environ["FACEFUSION_MODELS_PATH"] = self.model_dir
#         print(f"Set FACEFUSION_MODELS_PATH to {self.model_dir}")
        
#         # Verify models
#         missing = []
#         found = []
#         for model, desc in model_descriptions.items():
#             model_path = os.path.join(self.model_dir, model)
#             if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
#                 size_mb = os.path.getsize(model_path) / (1024 * 1024)
#                 found.append(f"{model} ({desc}, {size_mb:.2f}MB)")
#             else:
#                 missing.append(f"{model} ({desc})")
        
#         if missing:
#             print(f"Warning: Missing models: {', '.join(missing)}")
#         else:
#             print(f"All required models verified successfully in {self.model_dir}")
            
#         if found:
#             print(f"Found models: {', '.join(found)}")
        
#         # Print environment for debugging
#         print("Working directory:", os.getcwd())
        
#         # Check if the model directory exists and has files
#         if os.path.exists(self.model_dir):
#             model_files_found = os.listdir(self.model_dir)
#             print(f"Models directory contents ({len(model_files_found)} files):", model_files_found)
#         else:
#             print(f"Models directory does not exist: {self.model_dir}")
    
#     def predict(
#         self,
#         source: Path = Input(description="Source face image to use for swapping"),
#         target: Path = Input(description="Target image or video to apply face swap to"),
#         reference_face_position: int = Input(
#             description="Face position in source (0 = first face)",
#             default=0,
#             ge=0,
#             le=10
#         ),
#         reference_frame_number: int = Input(
#             description="Frame number to use as reference in videos",
#             default=46,
#             ge=0
#         ),
#         output_video_quality: int = Input(
#             description="Output video quality (1-100)",
#             default=80,
#             ge=1,
#             le=100
#         ),
#         output_video_fps: int = Input(
#             description="Output video framerate",
#             default=25,
#             ge=1,
#             le=60
#         ),
#         processors: str = Input(
#             description="Processors to use",
#             default="face_swapper,face_enhancer",
#             choices=["face_swapper", "face_swapper,face_enhancer"]
#         )
#     ) -> Path:
#         """Run face swap with FaceFusion."""
#         # Validate inputs
#         if not os.path.exists(source):
#             raise ValueError(f"Source file not found: {source}")
#         if not os.path.isfile(source):
#             raise ValueError(f"Source is not a file: {source}")
            
#         if not os.path.exists(target):
#             raise ValueError(f"Target file not found: {target}")
#         if not os.path.isfile(target):
#             raise ValueError(f"Target is not a file: {target}")
            
#         # Check for file types
#         source_ext = os.path.splitext(str(source))[1].lower()
#         if source_ext in ['.mp4', '.avi', '.mov', '.webm', '.gif', '.mkv']:
#             raise ValueError("Source must be an image file, not a video")
        
#         # Determine if target is image or video
#         target_extension = os.path.splitext(str(target))[1].lower()
#         is_video = target_extension in ['.mp4', '.avi', '.mov', '.webm', '.gif', '.mkv']
        
#         # Create output file
#         if is_video:
#             with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp:
#                 output_path = temp.name
#         else:
#             with tempfile.NamedTemporaryFile(suffix=target_extension, delete=False) as temp:
#                 output_path = temp.name
        
#         print(f"Processing {'video' if is_video else 'image'}: {target}")
#         print(f"Output will be saved to: {output_path}")
        
#         # Parse processors
#         processor_list = processors.split(',')
        
#         # Try to find facefusion.py
#         facefusion_script = None
#         for possible_path in ["facefusion.py", "/src/facefusion.py"]:
#             if os.path.exists(possible_path):
#                 facefusion_script = possible_path
#                 print(f"Found FaceFusion script at: {facefusion_script}")
#                 break
        
#         if not facefusion_script:
#             raise RuntimeError("Could not find facefusion.py script!")
        
#         # Add environment variables that might help FaceFusion find its models
#         env = os.environ.copy()
#         env["FACEFUSION_MODELS_PATH"] = self.model_dir
        
#         # Show progress information
#         print(f"[1/5] Preparing to process with FaceFusion...")
        
#         # Build command
#         cmd = [
#             "python", facefusion_script, "headless-run",
#             "-s", str(source),
#             "-t", str(target),
#             "-o", output_path,
#             "--face-detector-model", "yoloface_8n",
#             "--face-detector-size", "640x640",
#             "--face-detector-angles", "0", "90",
#             "--face-landmarker-model", "2dfan4",
#             "--face-landmarker-score", "0.5",
#             "--face-selector-mode", "reference",
#             "--face-selector-order", "large-small",
#             "--reference-face-position", str(reference_face_position),
#             "--reference-face-distance", "0.6",
#             "--reference-frame-number", str(reference_frame_number),
#             "--face-occluder-model", "xseg_1",
#             "--face-parser-model", "bisenet_resnet_34",
#             "--face-mask-types", "occlusion", "region",
#             "--temp-frame-format", "png",
#             "--output-image-quality", "80",
#             "--output-image-resolution", "1920x1080",
#             "--output-audio-encoder", "aac",
#             "--output-video-encoder", "libx264",
#             "--output-video-preset", "veryfast",
#             "--output-video-quality", str(output_video_quality),
#             "--output-video-resolution", "1080x720",
#             "--output-video-fps", str(output_video_fps),
#             "--processors"
#         ]
        
#         # Add processors dynamically
#         cmd.extend(processor_list)
        
#         # Add the rest of the command
#         cmd.extend([
#             "--face-enhancer-model", "gfpgan_1.4",
#             "--face-swapper-model", "inswapper_128",
#             "--execution-providers", "cuda",
#             "--execution-thread-count", "4",
#             "--execution-queue-count", "1",
#             "--download-providers", "github",
#             "--log-level", "info"
#         ])
        
#         print(f"[2/5] Running FaceFusion with command: {' '.join(cmd)}")
        
#         # Start processing timer
#         start_time = time.time()
        
#         # Execute command with real-time output monitoring and timeout
#         try:
#             process = subprocess.Popen(
#                 cmd,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#                 universal_newlines=True,
#                 env=env
#             )
            
#             print(f"[3/5] Processing content...")
            
#             # Monitor and print output in real-time with timeout
#             from threading import Thread
#             import queue
            
#             # Use queues to capture output safely
#             stdout_queue = queue.Queue()
#             stderr_queue = queue.Queue()
            
#             def read_stdout():
#                 for line in iter(process.stdout.readline, ""):
#                     if "%" in line:  # Progress line
#                         print(f"\r[4/5] Processing: {line.strip()}", end="")
#                     else:
#                         print(line.strip())
#                     stdout_queue.put(line)
#                 process.stdout.close()
            
#             def read_stderr():
#                 for line in iter(process.stderr.readline, ""):
#                     print(f"ERROR: {line.strip()}")
#                     stderr_queue.put(line)
#                 process.stderr.close()
            
#             # Start monitoring threads
#             stdout_thread = Thread(target=read_stdout, daemon=True)
#             stderr_thread = Thread(target=read_stderr, daemon=True)
#             stdout_thread.start()
#             stderr_thread.start()
            
#             # Wait with timeout
#             try:
#                 return_code = process.wait(timeout=600)  # 10 minute timeout
#             except subprocess.TimeoutExpired:
#                 process.kill()
#                 raise RuntimeError("FaceFusion process timed out after 10 minutes. Try a smaller video or image.")
            
#             # Print newline after progress reporting
#             print("")
            
#             # Check for specific errors
#             if return_code != 0:
#                 # Collect error output
#                 stderr_output = ""
#                 try:
#                     while not stderr_queue.empty():
#                         stderr_output += stderr_queue.get_nowait()
#                 except queue.Empty:
#                     pass
                
#                 if "CUDA out of memory" in stderr_output:
#                     raise RuntimeError("GPU ran out of memory. Try processing a smaller video or reducing resolution.")
#                 elif "No face detected" in stderr_output:
#                     raise ValueError("No faces could be detected in the source image. Please try another image.")
#                 else:
#                     raise RuntimeError(f"FaceFusion failed with error code {return_code}: {stderr_output}")
            
#             # Verify output file
#             print(f"[5/5] Verifying output file...")
#             if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
#                 raise RuntimeError(f"Output file not created or empty: {output_path}")
            
#             # Report processing time
#             processing_time = time.time() - start_time
#             print(f"Processing completed in {processing_time:.2f} seconds")
            
#             return Path(output_path)
            
#         except Exception as e:
#             print(f"Error during processing: {str(e)}")
#             # Clean up temp file if it exists
#             if os.path.exists(output_path):
#                 try:
#                     os.unlink(output_path)
#                 except:
#                     pass
#             raise

import os
import tempfile
import subprocess
import time
import shutil
import requests
from pathlib import Path as PathLib
from tqdm import tqdm
from cog import BasePredictor, Path, Input

class Predictor(BasePredictor):
    def setup(self):
        """Download models, verify, and prepare environment."""
        # Use .assets/models as the canonical location for models
        self.model_dir = ".assets/models"
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Model file URLs
        model_files = {
            "xseg_1.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.1.0/xseg_1.onnx",
            "bisenet_resnet_34.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/bisenet_resnet_34.onnx",
            "GFPGANv1.4.pth": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
            "inswapper_128.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/inswapper_128.onnx",
            "2dfan4.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/2dfan4.onnx",
            "yoloface_8n.onnx": "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/yoloface_8n.onnx"
        }
        
        # Model descriptions for reporting
        model_descriptions = {
            "yoloface_8n.onnx": "Face Detector",
            "2dfan4.onnx": "Face Landmarker",
            "inswapper_128.onnx": "Face Swapper",
            "GFPGANv1.4.pth": "Face Enhancer",
            "xseg_1.onnx": "Face Occluder",
            "bisenet_resnet_34.onnx": "Face Parser"
        }
        
        # Download models
        for model_file, url in model_files.items():
            model_path = os.path.join(self.model_dir, model_file)
            
            # Skip if model already exists
            if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
                print(f"Model {model_file} already exists")
                continue
            
            print(f"Downloading {model_file} from {url}...")
            
            try:
                # Stream download with progress reporting
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                # Get content length if available
                total_size = int(response.headers.get('content-length', 0))
                
                # Download with progress bar
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                temp_file.write(chunk)
                                pbar.update(len(chunk))
                    temp_path = temp_file.name
                
                # Move to final location
                shutil.move(temp_path, model_path)
                print(f"Successfully downloaded {model_file}")
            except Exception as e:
                print(f"Error downloading {model_file}: {str(e)}")
                if os.path.exists(model_path) and os.path.getsize(model_path) == 0:
                    os.remove(model_path)  # Remove empty file if download failed
        
        # Create a copy of yoloface_8n.onnx as yoloface.onnx
        source_path = os.path.join(self.model_dir, "yoloface_8n.onnx")
        target_path = os.path.join(self.model_dir, "yoloface.onnx")
        
        if os.path.exists(source_path) and not os.path.exists(target_path):
            try:
                shutil.copy2(source_path, target_path)
                print(f"Created copy of yoloface_8n.onnx as yoloface.onnx")
            except Exception as e:
                print(f"Warning: Failed to copy model: {str(e)}")
        
        # Set environment variables - point to .assets/models
        os.environ["FACEFUSION_MODELS_PATH"] = self.model_dir
        print(f"Set FACEFUSION_MODELS_PATH to {self.model_dir}")
        
        # Verify models
        missing = []
        found = []
        for model, desc in model_descriptions.items():
            model_path = os.path.join(self.model_dir, model)
            if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
                size_mb = os.path.getsize(model_path) / (1024 * 1024)
                found.append(f"{model} ({desc}, {size_mb:.2f}MB)")
            else:
                missing.append(f"{model} ({desc})")
        
        if missing:
            print(f"Warning: Missing models: {', '.join(missing)}")
        else:
            print(f"All required models verified successfully in {self.model_dir}")
            
        if found:
            print(f"Found models: {', '.join(found)}")
        
        # Print environment for debugging
        print("Working directory:", os.getcwd())
        
        # Check if the model directory exists and has files
        if os.path.exists(self.model_dir):
            model_files_found = os.listdir(self.model_dir)
            print(f"Models directory contents ({len(model_files_found)} files):", model_files_found)
        else:
            print(f"Models directory does not exist: {self.model_dir}")
    
    def predict(
        self,
        source: Path = Input(description="Source face image to use for swapping"),
        target: Path = Input(description="Target image or video to apply face swap to"),
        reference_face_position: int = Input(
            description="Face position in source (0 = first face)",
            default=0,
            ge=0,
            le=10
        ),
        reference_frame_number: int = Input(
            description="Frame number to use as reference in videos",
            default=46,
            ge=0
        ),
        output_video_quality: int = Input(
            description="Output video quality (1-100)",
            default=80,
            ge=1,
            le=100
        ),
        output_video_fps: int = Input(
            description="Output video framerate",
            default=25,
            ge=1,
            le=60
        ),
        processors: str = Input(
            description="Processors to use",
            default="face_swapper,face_enhancer",
            choices=["face_swapper", "face_swapper,face_enhancer"]
        )
    ) -> Path:
        """Run face swap with FaceFusion."""
        # Validate inputs
        if not os.path.exists(source):
            raise ValueError(f"Source file not found: {source}")
        if not os.path.isfile(source):
            raise ValueError(f"Source is not a file: {source}")
            
        if not os.path.exists(target):
            raise ValueError(f"Target file not found: {target}")
        if not os.path.isfile(target):
            raise ValueError(f"Target is not a file: {target}")
            
        # Check for file types
        source_ext = os.path.splitext(str(source))[1].lower()
        if source_ext in ['.mp4', '.avi', '.mov', '.webm', '.gif', '.mkv']:
            raise ValueError("Source must be an image file, not a video")
        
        # Determine if target is image or video
        target_extension = os.path.splitext(str(target))[1].lower()
        is_video = target_extension in ['.mp4', '.avi', '.mov', '.webm', '.gif', '.mkv']
        
        # # Create output file
        # if is_video:
        #     with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp:
        #         output_path = temp.name
        # else:
        #     with tempfile.NamedTemporaryFile(suffix=target_extension, delete=False) as temp:
        #         output_path = temp.name

        # Generate dynamic output filename
        if is_video:
            # For videos, use .mp4 extension
            source_name = os.path.splitext(os.path.basename(str(source)))[0]
            target_name = os.path.splitext(os.path.basename(str(target)))[0]
            timestamp = int(time.time())
            output_filename = f"{source_name}_on_{target_name}_{timestamp}.mp4"
            output_path = os.path.join(tempfile.gettempdir(), output_filename)
        else:
            # For images, use the same extension as the target image
            source_name = os.path.splitext(os.path.basename(str(source)))[0]
            target_name = os.path.splitext(os.path.basename(str(target)))[0]
            target_extension = os.path.splitext(str(target))[1].lower()
            
            # If target extension is unusual, default to .png
            if target_extension not in ['.jpg', '.jpeg', '.png', '.webp']:
                target_extension = '.png'
                
            timestamp = int(time.time())
            output_filename = f"{source_name}_on_{target_name}_{timestamp}{target_extension}"
            output_path = os.path.join(tempfile.gettempdir(), output_filename)
        
        print(f"Processing {'video' if is_video else 'image'}: {target}")
        print(f"Output will be saved to: {output_path}")
        
        # Parse processors
        processor_list = processors.split(',')
        
        # Try to find facefusion.py
        facefusion_script = None
        for possible_path in ["facefusion.py", "/src/facefusion.py"]:
            if os.path.exists(possible_path):
                facefusion_script = possible_path
                print(f"Found FaceFusion script at: {facefusion_script}")
                break
        
        if not facefusion_script:
            raise RuntimeError("Could not find facefusion.py script!")
        
        # Add environment variables that might help FaceFusion find its models
        env = os.environ.copy()
        env["FACEFUSION_MODELS_PATH"] = self.model_dir
        
        # Show progress information
        print(f"[1/5] Preparing to process with FaceFusion...")
        
        # Build command
        cmd = [
            "python", facefusion_script, "headless-run",
            "-s", str(source),
            "-t", str(target),
            "-o", output_path,
            "--face-detector-model", "yoloface",  # Changed from yoloface_8n
            "--face-detector-size", "640x640",
            "--face-detector-angles", "0", "90",
            "--face-landmarker-model", "2dfan4",
            "--face-landmarker-score", "0.5",
            "--face-selector-mode", "reference",
            "--face-selector-order", "large-small",
            "--reference-face-position", str(reference_face_position),
            "--reference-face-distance", "0.6",
            "--reference-frame-number", str(reference_frame_number),
            "--face-occluder-model", "xseg_1",
            "--face-parser-model", "bisenet_resnet_34",
            "--face-mask-types", "occlusion", "region",
            "--temp-frame-format", "png",
            "--output-image-quality", "80",
            "--output-image-resolution", "1920x1080",
            "--output-audio-encoder", "aac",
            "--output-video-encoder", "libx264",
            "--output-video-preset", "veryfast",
            "--output-video-quality", str(output_video_quality),
            "--output-video-resolution", "1080x720",
            "--output-video-fps", str(output_video_fps),
            "--processors"
        ]
        
        # Add processors dynamically
        cmd.extend(processor_list)
        
        # Add the rest of the command
        cmd.extend([
            "--face-enhancer-model", "gfpgan_1.4",
            "--face-swapper-model", "inswapper_128",
            "--execution-providers", "cuda",
            "--execution-thread-count", "4",
            "--execution-queue-count", "1",
            # "--download-providers", "github",
            "--log-level", "debug"
            #"--log-level", "info"
        ])
        
        print(f"[2/5] Running FaceFusion with command: {' '.join(cmd)}")
        
        # Start processing timer
        start_time = time.time()
        
        # Execute command with real-time output monitoring and timeout
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env
            )
            
            print(f"[3/5] Processing content...")
            
            # Monitor and print output in real-time with timeout
            from threading import Thread
            import queue
            
            # Use queues to capture output safely
            stdout_queue = queue.Queue()
            stderr_queue = queue.Queue()
            
            def read_stdout():
                for line in iter(process.stdout.readline, ""):
                    if "%" in line:  # Progress line
                        print(f"\r[4/5] Processing: {line.strip()}", end="")
                    else:
                        print(line.strip())
                    stdout_queue.put(line)
                process.stdout.close()
            
            def read_stderr():
                for line in iter(process.stderr.readline, ""):
                    print(f"ERROR: {line.strip()}")
                    stderr_queue.put(line)
                process.stderr.close()
            
            # Start monitoring threads
            stdout_thread = Thread(target=read_stdout, daemon=True)
            stderr_thread = Thread(target=read_stderr, daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            
            # # Wait with timeout
            # try:
            #     return_code = process.wait(timeout=600)  # 10 minute timeout
            # except subprocess.TimeoutExpired:
            #     process.kill()
            #     raise RuntimeError("FaceFusion process timed out after 10 minutes. Try a smaller video or image.")

            # Wait for process to complete (no timeout)
            return_code = process.wait()            
            
            # Print newline after progress reporting
            print("")
            
            # Check for specific errors
            if return_code != 0:
                # Collect error output
                stderr_output = ""
                try:
                    while not stderr_queue.empty():
                        stderr_output += stderr_queue.get_nowait()
                except queue.Empty:
                    pass
                
                if "CUDA out of memory" in stderr_output:
                    raise RuntimeError("GPU ran out of memory. Try processing a smaller video or reducing resolution.")
                elif "No face detected" in stderr_output:
                    raise ValueError("No faces could be detected in the source image. Please try another image.")
                else:
                    raise RuntimeError(f"FaceFusion failed with error code {return_code}: {stderr_output}")
            
            # Verify output file
            print(f"[5/5] Verifying output file...")
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise RuntimeError(f"Output file not created or empty: {output_path}")
            
            # Report processing time
            processing_time = time.time() - start_time
            print(f"Processing completed in {processing_time:.2f} seconds")
            
            return Path(output_path)
            
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            # Clean up temp file if it exists
            if os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except:
                    pass
            raise