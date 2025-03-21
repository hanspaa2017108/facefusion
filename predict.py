import os
import tempfile
import subprocess
import time
from pathlib import Path as PathLib
from cog import BasePredictor, Path, Input

class Predictor(BasePredictor):
    def setup(self):
        """Prepare environment."""
        print("Working directory:", os.getcwd())
        print("Setting up FaceFusion for video processing...")
    
    def predict(
        self,
        source: Path = Input(description="Source face image to use for swapping"),
        target: Path = Input(description="Target image or video to apply face swap to"),
        
        # Face Detection Parameters
        face_detector_model: str = Input(
            description="Face detector model to use",
            default="yoloface",
            choices=["many", "retinaface", "scrfd", "yoloface"]
        ),
        face_detector_size: str = Input(
            description="Face detector size",
            default="640x640",
            choices=["640x640"]
        ),
        face_detector_score: float = Input(
            description="Minimum face detector confidence score",
            default=0.5,
            ge=0.0,
            le=1.0
        ),
        face_detector_angles: str = Input(
            description="Face detector angles (comma-separated: 0,90,180,270)",
            default="0,90"
        ),
        
        # Face Landmark Parameters
        face_landmarker_model: str = Input(
            description="Face landmarker model to use",
            default="2dfan4",
            choices=["many", "2dfan4", "peppa_wutz"]
        ),
        face_landmarker_score: float = Input(
            description="Minimum face landmarker confidence score",
            default=0.5,
            ge=0.0,
            le=1.0
        ),
        
        # Face Selection Parameters
        face_selector_mode: str = Input(
            description="Face selector mode",
            default="reference",
            choices=["many", "one", "reference"]
        ),
        face_selector_order: str = Input(
            description="Face selector order",
            default="large-small",
            choices=["left-right", "right-left", "top-bottom", "bottom-top", "small-large", "large-small", "best-worst", "worst-best"]
        ),
        reference_face_position: int = Input(
            description="Face position in source (0 = first face)",
            default=0,
            ge=0
        ),
        reference_face_distance: float = Input(
            description="Reference face distance threshold",
            default=0.6,
            ge=0.0,
            le=1.0
        ),
        reference_frame_number: int = Input(
            description="Frame number to use as reference in videos",
            default=0,
            ge=0
        ),
        
        # Face Masking and Parsing Parameters
        face_occluder_model: str = Input(
            description="Face occluder model",
            default="xseg_1",
            choices=["xseg_1", "xseg_2"]
        ),
        face_parser_model: str = Input(
            description="Face parser model",
            default="bisenet_resnet_34",
            choices=["bisenet_resnet_18", "bisenet_resnet_34"]
        ),
        face_mask_types: str = Input(
            description="Face mask types (comma-separated)",
            default="box",
            choices=["box", "occlusion", "region", "box,occlusion", "box,region", "occlusion,region", "box,occlusion,region"]
        ),
        face_mask_blur: float = Input(
            description="Face mask blur amount",
            default=0.0,
            ge=0.0,
            le=1.0
        ),
        face_mask_padding: str = Input(
            description="Face mask padding in pixels (top,right,bottom,left or single value for all)",
            default="0,0,0,0"
        ),
        face_mask_regions: str = Input(
            description="Face mask regions (comma-separated)",
            default=""
        ),
        
        # Video Processing Parameters
        trim_frame_start: int = Input(
            description="First frame to process in video",
            default=0,
            ge=0
        ),
        trim_frame_end: int = Input(
            description="Last frame to process in video (0 = until end)",
            default=0,
            ge=0
        ),
        temp_frame_format: str = Input(
            description="Temporary frame format for processing",
            default="png",
            choices=["bmp", "jpg", "png"]
        ),
        keep_temp: bool = Input(
            description="Keep temporary files after processing",
            default=False
        ),
        
        # Processor Parameters
        processors: str = Input(
            description="Processors to use (comma-separated)",
            default="face_swapper,face_enhancer",
            choices=["face_swapper", "face_enhancer", "face_swapper,face_enhancer"]
        ),
        skip_audio: bool = Input(
            description="Skip audio processing",
            default=False
        ),
        
        # Output Video Parameters
        output_video_fps: float = Input(
            description="Output video framerate",
            default=25.0,
            ge=0.1
        ),
        output_video_resolution: str = Input(
            description="Output video resolution (WIDTHxHEIGHT or 'original')",
            default="original"
        ),
        output_video_quality: int = Input(
            description="Output video quality (0-100, higher is better)",
            default=80,
            ge=0,
            le=100
        ),
        output_video_preset: str = Input(
            description="Output video preset (affects encoding speed/quality)",
            default="veryfast",
            choices=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
        ),
        output_video_encoder: str = Input(
            description="Video encoder for output",
            default="libx264",
            choices=[
                "libx264", "libx265", "libvpx-vp9", "h264_nvenc", "hevc_nvenc", 
                "h264_amf", "hevc_amf", "h264_qsv", "hevc_qsv", 
                "h264_videotoolbox", "hevc_videotoolbox"
            ]
        ),
        
        # Output Audio Parameters
        output_audio_encoder: str = Input(
            description="Audio encoder for output",
            default="aac",
            choices=["aac", "libmp3lame", "libopus", "libvorbis"]
        ),
        
        # Output Image Parameters
        output_image_resolution: str = Input(
            description="Output image resolution (WIDTHxHEIGHT or 'original')",
            default="original"
        ),
        output_image_quality: int = Input(
            description="Output image quality (0-100, higher is better)",
            default=80,
            ge=0,
            le=100
        ),
        
        # Model Selection Parameters
        face_swapper_model: str = Input(
            description="Face swapper model to use",
            default="inswapper_128",
            choices=[
                "blendswap_256", "ghost_1_256", "ghost_2_256", "ghost_3_256",
                "hififace_unofficial_256", "inswapper_128", "inswapper_128_fp16",
                "simswap_256", "simswap_unofficial_512", "uniface_256"
            ]
        ),
        face_enhancer_model: str = Input(
            description="Face enhancer model to use",
            default="gfpgan_1.4",
            choices=[
                "codeformer", "gfpgan_1.2", "gfpgan_1.3", "gfpgan_1.4",
                "gpen_bfr_256", "gpen_bfr_512", "gpen_bfr_1024", "gpen_bfr_2048",
                "restoreformer_plus_plus"
            ]
        ),
        
        # Execution Parameters
        execution_providers: str = Input(
            description="Execution providers for processing",
            default="cuda",
            choices=["cpu", "cuda", "coreml"]
        ),
        execution_thread_count: int = Input(
            description="Number of execution threads",
            default=4,
            ge=1,
            le=128
        ),
        execution_queue_count: int = Input(
            description="Number of execution queues",
            default=1,
            ge=1,
            le=32
        ),
        
        # Other Parameters
        log_level: str = Input(
            description="Logging verbosity level",
            default="info",
            choices=["error", "warn", "info", "debug"]
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
        
        # Parse list-type parameters
        face_detector_angles_list = face_detector_angles.split(',')
        face_mask_types_list = face_mask_types.split(',')
        processor_list = processors.split(',')
        face_mask_padding_list = face_mask_padding.split(',')
        face_mask_regions_list = face_mask_regions.split(',') if face_mask_regions else []
        
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
        
        # Show progress information
        print(f"[1/5] Preparing to process with FaceFusion...")
        
        # Build command
        cmd = [
            "python", facefusion_script, "headless-run",
            "-s", str(source),
            "-t", str(target),
            "-o", output_path,
            "--face-detector-model", face_detector_model,
            "--face-detector-size", face_detector_size,
            "--face-detector-score", str(face_detector_score)
        ]
        
        # Add face detector angles
        cmd.append("--face-detector-angles")
        cmd.extend(face_detector_angles_list)
        
        # Add face landmarker parameters
        cmd.extend([
            "--face-landmarker-model", face_landmarker_model,
            "--face-landmarker-score", str(face_landmarker_score),
            "--face-selector-mode", face_selector_mode,
            "--face-selector-order", face_selector_order,
            "--reference-face-position", str(reference_face_position),
            "--reference-face-distance", str(reference_face_distance)
        ])
        
        # Add reference frame number if it's a video
        if is_video and reference_frame_number > 0:
            cmd.extend(["--reference-frame-number", str(reference_frame_number)])
        
        # Add face occluder and parser models
        cmd.extend([
            "--face-occluder-model", face_occluder_model,
            "--face-parser-model", face_parser_model
        ])
        
        # Add face mask types
        cmd.append("--face-mask-types")
        cmd.extend(face_mask_types_list)
        
        # Add face mask blur if non-zero
        if face_mask_blur > 0:
            cmd.extend(["--face-mask-blur", str(face_mask_blur)])
        
        # # Add face mask padding if not default
        # if face_mask_padding != "0,0,0,0":
        #     cmd.append("--face-mask-padding")
        #     cmd.extend(face_mask_padding_list)

        # Only add face mask padding if "box" is in the selected mask types and padding is not default
        if "box" in face_mask_types_list and face_mask_padding != "0,0,0,0":
            cmd.append("--face-mask-padding")
            cmd.extend(face_mask_padding_list)        
        
        # Add face mask regions if specified
        if face_mask_regions_list:
            cmd.append("--face-mask-regions")
            cmd.extend(face_mask_regions_list)
        
        # Add trim frame parameters if specified
        if trim_frame_start > 0:
            cmd.extend(["--trim-frame-start", str(trim_frame_start)])
        
        if trim_frame_end > 0:
            cmd.extend(["--trim-frame-end", str(trim_frame_end)])
        
        # Add temp frame format
        cmd.extend(["--temp-frame-format", temp_frame_format])
        
        # Add keep temp flag if specified
        if keep_temp:
            cmd.append("--keep-temp")
        
        # Add output parameters
        if output_image_resolution != "original":
            cmd.extend(["--output-image-resolution", output_image_resolution])
        
        cmd.extend(["--output-image-quality", str(output_image_quality)])
        
        if is_video:
            if output_video_resolution != "original":
                cmd.extend(["--output-video-resolution", output_video_resolution])
            
            cmd.extend([
                "--output-video-encoder", output_video_encoder,
                "--output-video-quality", str(output_video_quality),
                "--output-video-preset", output_video_preset,
                "--output-video-fps", str(output_video_fps),
                "--output-audio-encoder", output_audio_encoder
            ])
        
        # Add skip audio flag if specified
        if skip_audio:
            cmd.append("--skip-audio")
        
        # Add processors
        cmd.append("--processors")
        cmd.extend(processor_list)
        
        # Add face enhancer and swapper models
        cmd.extend([
            "--face-enhancer-model", face_enhancer_model,
            "--face-swapper-model", face_swapper_model
        ])
        
        # Add execution parameters
        cmd.extend([
            "--execution-providers", execution_providers,
            "--execution-thread-count", str(execution_thread_count),
            "--execution-queue-count", str(execution_queue_count),
            "--log-level", log_level
        ])
        
        print(f"[2/5] Running FaceFusion with command: {' '.join(cmd)}")
        
        # Start processing timer
        start_time = time.time()
        
        # Execute command with real-time output monitoring
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env
            )
            
            print(f"[3/5] Processing content...")
            
            # Monitor and print output in real-time
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