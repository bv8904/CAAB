# Child-Aware Application Blocker (CAAB): A Context-Aware Parental Control Framework

## 1. Abstract
The Child-Aware Application Blocker (CAAB) project presents a context-aware system designed to enhance parental control by dynamically restricting access to specific applications based on the user's age category. Utilizing computer vision and machine learning (MobileNetV2), CAAB monitors the active user via a webcam and automatically terminates predefined blocked processes if the user is identified as a minor. This paper outlines the system's architecture, including its real-time monitoring, facial age classification, and process management modules, highlighting its efficacy as an intelligent, responsive, and non-intrusive parental control solution.

## 2. Introduction
With the proliferation of digital devices in households, ensuring children's safety and regulating their access to age-inappropriate content or applications has become a paramount concern for parents. Traditional parental control software often relies on static passwords or time-based restrictions, failing to account for physical situations where a child might access an already-unlocked device. 

The Child-Aware Application Blocker (CAAB) addresses this limitation by introducing a dynamic, computer-vision-based approach. By continuously monitoring the visual context of the user, CAAB leverages deep learning to distinguish between adults and children in real-time, enforcing access policies dynamically. This paper details the architecture, working mechanism, and underlying research methodology of the CAAB framework.

## 3. Architecture
The CAAB system comprises five primary interconnected components implemented within a multithreaded Python environment:

1. **User Interface (UI Dashboard)**: Built using `CustomTkinter`, it provides a centralized dashboard for system status monitoring, recent log generation, and manual overrides (such as initiating a simulation mode).
2. **Process Manager**: Responsible for continuous system scanning. It utilizes the `psutil` library to detect the execution of blacklisted applications (e.g., web browsers, specific gaming platforms) and issues OS-level termination signals when unauthorized access is identified.
3. **Camera Service**: Manages the continuous video feed. It captures real-time frames from the system's primary webcam using OpenCV. This service runs continuously in a dedicated thread to ensure non-blocking UI and monitoring performance.
4. **Machine Learning Engine**: The core analytical intelligence. A pre-trained convolutional neural network processes normalized camera frames to classify the user into binary risk categories: 'Child' (under 18) or 'Adult'.
5. **Auxiliary Services (AdminAuth & SoundManager)**: The AdminAuth module handles secure PIN-based authentication required for modifying core system settings. The SoundManager provides immediate auditory feedback (alert chimes) upon successful application blocking actions.

## 4. Working
The system's operational flow is dictated by a background logical loop (daemon thread) that functions asynchronously alongside the UI. The workflow per cycle is as follows:

1. **Process Scanning**: The Process Manager queries the OS for active processes that match the predefined blocklist loaded from `config.py`.
2. **Visual Data Acquisition**: If a blocked application is found running, the system engages the Camera Service to fetch the most recent video frame of the current user.
3. **Inference pipeline**: The frame is pre-processed (down-sampled to 224x224 and normalized) and passed into the ML Engine.
4. **Classification**: The ML Engine evaluates the facial features within the frame, returning a classification identifying whether the user is a Child (Class 0) or an Adult (Class 1).
5. **Policy Enforcement**: 
   - If the user is identified as a **Child**, the Process Manager immediately terminates the unauthorized process. The action is logged to the dashboard and an auditory alert is triggered.
   - If an **Adult** is detected, the application is allowed to execute uninterrupted.
6. **Simulation**: A built-in simulation mode allows administrators to validate the logic pathways (blocking vs. allowing) without active camera utilization by manually toggling the perceived user status.

## 5. Research Methodology
The central facial analysis model was developed using a supervised transfer learning approach applied to the UTKFace dataset, a large-scale collection of images annotated with age constraints.

- **Data Curation**: The dataset was logically partitioned into two discrete classes: 'child' (ages 0-17) and 'adult' (ages 18+). An 80/20 train-validation split was established, employing stratified sampling to maintain class distribution integrity. 
- **Model Selection**: The system utilizes the **MobileNetV2** architecture, selected explicitly for its computational efficiency and parameter economy, making it highly suitable for real-time edge inference on standard consumer hardware.
- **Training Strategy**: The base ImageNet weights were initially frozen. A custom classification top—incorporating Global Average Pooling, a Dropout layer to mitigate overfitting (rate: 0.3), and a final Dense layer with a sigmoid activation function—was appended. 
- **Optimization**: The model was trained using Binary Cross-Entropy loss and the Adam optimizer (learning rate: 0.001). Real-time data augmentation (rotation, shifting, and flipping) was applied to the training set to enhance the model's spatial generalization capabilities. Robust training callbacks, including `ModelCheckpoint`, `EarlyStopping`, and `ReduceLROnPlateau`, were implemented to ensure convergence and retain optimal weights.

## 6. Conclusion and Findings
The development of the CAAB framework successfully demonstrates a viable and highly responsive solution for intelligent, physical access control based on user demographics. The integration of continuous visual context significantly addresses the shortcomings of static, password-based parental controls.

**Key Findings:**
1. The employment of lightweight architectural frameworks like MobileNetV2 permits near-instantaneous inference (real-time operation) without imposing heavy computational overhead on the host machine.
2. Direct integration of inference outputs with OS-level process management facilitates a seamless, automated security layer that operates independently of user input once configured.

**Future Scope:**
Subsequent iterations of the framework could benefit from enhanced robustness by explicitly addressing edge cases, such as multiple faces within a single frame and highly variable lighting conditions. Additionally, the incorporation of facial anti-spoofing (liveness detection) mechanisms is recommended to prevent system circumvention via static imagery.
