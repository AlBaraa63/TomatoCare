# TomatoCare ML Presentation Guide & Q&A Blueprint

This guide is designed for your capstone presentation. It breaks down the entire Machine Learning section into simple, easy-to-explain concepts, tells you exactly what to say for each slide, and prepares you for any questions the examiners might ask.

---

## 🗺️ The ML Section Overview (The Big Picture)

When presenting, use this simple roadmap to explain your machine learning system:

```mermaid
graph TD
    A[1. INPUT IMAGE] --> B[Leaf Gate: Is it a leaf?]
    B -->|Yes| C[Tomato Gate: Is it a tomato leaf?]
    B -->|No| Reject[REJECT: "Not a leaf!"]
    C -->|Yes| D[Disease Classifier: 11 Classes]
    C -->|No| Reject2[REJECT: "Not a tomato leaf!"]
    D --> E[Calibrated Confidence: Scale probability]
    E --> F[Android TFLite Model: Float16 quantized]
```

### 🗣️ Core Elevator Pitch (What to say at the start):
> *"Instead of building a simple, fragile model that tries to diagnose everything it sees, we built a highly robust **3-Stage Cascade System**. The system acts like security gates: it rejects non-leaf objects first, then rejects non-tomato leaves, and only classifies the disease once it is 100% sure it's looking at a tomato leaf. Finally, we used Temperature Scaling to calibrate confidence scores and Float16 Quantization to make the model run smoothly on a phone."*

---

## 🛠️ Part 1: The Deployed 3-Stage Cascade (Why and How)

### 1. What is the Cascade?
Instead of a single neural network, your app runs **three models in sequence**:

| Stage | Model | Purpose | Size |
| :--- | :--- | :--- | :--- |
| **1. Leaf Gate** | MobileNetV3-Small | Rejects random objects (hand, sky, table, etc.) | **1.92 MB** |
| **2. Tomato Gate** | MobileNetV3-Small | Rejects non-tomato leaves (rose, basil, grape, etc.) | **1.92 MB** |
| **3. Disease Classifier** | MobileNetV3-Large | Classifies the leaf into 10 diseases + 1 healthy class | **6.03 MB** |

* **Total size:** **9.87 MB** (Very lightweight and fits on any budget phone!).

---

### 2. Why is this better than a single model? (Crucial for Examiners!)
* **The Problem with Single Models:** If you train a single model on tomato diseases, and you show it a photo of a dog, a car, or a rose leaf, the model **must** choose one of the tomato disease categories. It will confidently output something like *"Tomato Late Blight: 95% Confidence"*. 
* **The Cascade Solution:** The cascade intercepts the image. If Stage 1 or Stage 2 says "No", the pipeline halts and alerts the user.

---

### 🗣️ Presentation Script (What to say):
> *"One of our key design innovations is the **3-Stage Cascade**. A common issue with mobile vision apps is that if a user points the camera at a shoe or a rose leaf, a standard model will try to classify it as a tomato disease. By placing a Leaf Gate and a Tomato Gate before the actual Disease Classifier, we reject invalid inputs before they ever reach the final model. This ensures our app only gives tomato diagnoses on real tomato leaves."*

---

## 📈 Part 2: The 7-Step Training & Deployment Pipeline

You have 7 main scripts under [`ml/scripts/`](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/scripts/). They tell a step-by-step story of how you train, calibrate, evaluate, and package all three models.

### Step 1: [step1_train_leaf_gate.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/scripts/step1_train_leaf_gate.py) (Leaf Gate Training)
* **What it does:** Trains the Leaf Gate model (`MobileNetV3-Small` backbone) on images containing leaf and non-leaf objects (hand, sky, table) using two-phase transfer learning.
* **🗣️ What to say:**
  > *"In Step 1, we train our first binary model—the Leaf Gate. This model learns to recognize whether an image contains a leaf at all, acting as our first line of defense to reject random background photos."*

### Step 2: [step2_train_tomato_gate.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/scripts/step2_train_tomato_gate.py) (Tomato Gate Training)
* **What it does:** Trains the Tomato Gate model (`MobileNetV3-Small` backbone) to differentiate between real tomato leaves and other plant species (rose, grape, weeds).
* **🗣️ What to say:**
  > *"In Step 2, we train the Tomato Gate. This is our second binary model, which determines if the detected leaf is actually a tomato leaf. It prevents the model from attempting to diagnose diseases on weeds or other crops."*

### Step 3: [step3_train_disease_stage1.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/scripts/step3_train_disease_stage1.py) (Disease Classifier - Head Training)
* **What it does:** Freezes the pretrained `MobileNetV3-Large` backbone and trains only our custom Dense classifier layer (the "head") to recognize the 11 classes (10 diseases + healthy).
* **🗣️ What to say:**
  > *"In Step 3, we build the main Disease Classifier. We use Transfer Learning by loading Google's pre-trained MobileNetV3-Large model and freezing its weights, training only our custom classification layers on top."*

### Step 4: [step4_train_disease_stage2.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/scripts/step4_train_disease_stage2.py) (Disease Classifier - Fine-Tuning)
* **What it does:** Unfreezes the top 30 layers of the backbone and trains them at a very low learning rate ($0.0001$) to specialize its features to tomato lesions.
* **🗣️ What to say:**
  > *"In Step 4, we fine-tune the classifier. We unfreeze the top 30 backbone layers and train them at a very low learning rate, letting the model's visual sensors adjust to the fine spots and textures of tomato diseases."*

### Step 5: [step5_calibrate_temperature.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/scripts/step5_calibrate_temperature.py) (Temperature Calibration)
* **What it does:** Optimizes a temperature scalar $T$ ($0.5889$) and inserts a division layer directly before softmax to fix model overconfidence.
* **🗣️ What to say:**
  > *"In Step 5, we perform Temperature Calibration. By scaling the raw output scores directly inside the model architecture, we ensure the confidence percentages shown on the phone are statistically reliable."*

### Step 6: [step6_eval_model.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/scripts/step6_eval_model.py) (Evaluation & QA Gates)
* **What it does:** Runs evaluation on the test dataset to verify accuracy ($97.59\%$), macro F1, and ECE against hard quality control gates.
* **🗣️ What to say:**
  > *"In Step 6, we run comprehensive testing. The model is evaluated on unseen test data and must satisfy strict Quality Assurance gates, like hitting at least 90% accuracy, before it can proceed."*

### Step 7: [step7_export_tflite.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/scripts/step7_export_tflite.py) (TFLite Export)
* **What it does:** Converts Keras models to TensorFlow Lite using Float16 quantization, reducing size to under 10MB total.
* **🗣️ What to say:**
  > *"Finally, in Step 7, we export our models into TensorFlow Lite format using Float16 quantization. This compresses the files to under 10MB so they run smoothly on budget Android phones."*

---

## 🔬 Part 3: The Scientific Rigor (Your Experiments)

These are investigations you ran to prove your design choices. They demonstrate academic depth.

### 1. Leaf Segmentation ([step1_segment_leaves.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/experiments/step1_segment_leaves.py))
* **What it does:** Uses Meta's pre-trained **MobileSAM** to crop out leaves.
* **Purpose:** Proving whether removing backgrounds forces the classifier to focus entirely on leaf shape/lesions.

### 2. Generative Data Augmentation (GANs) ([step2_gan_dcgan.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/experiments/step2_gan_dcgan.py) & [step3_gan_field_eval.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/experiments/step3_gan_field_eval.py))
* **What it does:** Trains a Deep Convolutional GAN (DCGAN) to generate synthetic tomato leaves to solve class imbalances for rare/weak classes.
* **Finding:** While GANs generated realistic images, they did not significantly boost accuracy on real field data, showing that real-world field-testing data is superior to synthetic images.

### 3. Background Composite Robustness ([step4_composite_eval.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/experiments/step4_composite_eval.py))
* **What it does:** Pastes studio-background leaves onto messy, real-world farm backgrounds.
* **Finding:** Helped evaluate the **domain gap** (the difference between clean laboratory datasets and messy real-world farm photos).

### 4. Hard Negative Stress Test ([step6_hard_negative_test.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/experiments/step6_hard_negative_test.py))
* **What it does:** Feeds the model pictures of other plants (rose, grape) and random objects.
* **Finding:** Proved that our Leaf and Tomato Gates successfully reject invalid items $99.5\%$ of the time.

### 5. Confidence Threshold Sweep ([step7_threshold_sweep.py](file:///c:/Users/POTATO/Desktop/capstone/TomatoCare/ml/experiments/step7_threshold_sweep.py))
* **What it does:** Compares prediction accuracy against coverage.
* **Finding:** Mathematically justified setting the app's warning threshold to **60%**. Below 60%, the app warns the user that the image quality is too low for a reliable prediction.

---

## 🙋‍♂️ Part 4: Examiner Q&A Defense Blueprint

Here are the most common tough questions examiners ask and exactly how to answer them.

### Q1: Why did you choose MobileNetV3 instead of ResNet, EfficientNet, or YOLO?
* **Low-quality answer:** *"Because it was easy/standard."*
* **Pro-level answer (Use this):** 
  > *"We chose MobileNetV3 because our target platform is Android. MobileNetV3 uses **depthwise separable convolutions** and **squeeze-and-excite blocks**, making it extremely lightweight and optimized specifically for mobile CPUs. Heavier networks like ResNet or EfficientNet would make the app slow and drain the phone battery. YOLO is an object detection model, which requires bounding box annotations and is computationally heavier, whereas our core task is image classification, which only requires categorizing the image."*

### Q2: What is the "domain gap" and why did your model's accuracy drop from 97% in the lab to 77% in the field?
* **Low-quality answer:** *"Field images are just harder."*
* **Pro-level answer (Use this):** 
  > *"The domain gap refers to the difference in distribution between our training data (which consists of clean, well-lit laboratory photos with uniform backgrounds, like PlantVillage) and real-world farm environments (which have motion blur, shadows, complex soil backgrounds, and camera glare). We measured this drop scientifically (using PlantDoc field images) and found a 20% gap. To combat this, we implement the 3-stage cascade gate system and plan to use an in-app feedback flywheel to collect real-world images to continually fine-tune the model."*

### Q3: Why did you use Temperature Scaling instead of just taking the default Softmax outputs?
* **Low-quality answer:** *"To make the numbers better."*
* **Pro-level answer (Use this):** 
  > *"Modern deep neural networks are notoriously overconfident due to over-parameterization and weight decay. The default Softmax probabilities are not well-calibrated; a model might give a 99% probability on an incorrect class. Temperature scaling optimizes a single parameter $T$ on the validation set to scale logits without changing the class prediction. This aligns the confidence scores with empirical accuracy, making the app's 60% confidence threshold statistically reliable for farmers."*

### Q4: Why did you choose Float16 quantization instead of Int8 quantization?
* **Low-quality answer:** *"Float16 was better."*
* **Pro-level answer (Use this):** 
  > *"We evaluated both. Int8 quantization compresses the model to a smaller size, but because tomato diseases have fine-grained textures (like tiny leaf spots), the loss of precision caused our per-class accuracy to drop by 2% to 4%. Float16 quantization cut our model size in half (totaling 9.87 MB for all 3 models combined), while maintaining accuracy losses under 0.5%. Since our budget was 15 MB, Float16 was the optimal engineering trade-off."*

### Q5: How does your model handle images that are not tomato leaves at all?
* **Low-quality answer:** *"It has a class for it."*
* **Pro-level answer (Use this):** 
  > *"We handle this using the first two stages of our cascade: the Leaf Gate (which filters out non-leaf objects like hands, soil, or tables) and the Tomato Gate (which filters out non-tomato leaves like grapes or weeds). In our hard negative experiments, these gates rejected invalid inputs with over 99% accuracy, protecting the final disease classifier from garbage inputs."*

### Q6: Why did you use Class Weights during training?
* **Low-quality answer:** *"To make training balanced."*
* **Pro-level answer (Use this):** 
  > *"Our dataset is naturally imbalanced—some diseases have thousands of images, while rare ones have only a few hundred. Without class weights, the model would bias its predictions toward the larger classes to minimize loss. By applying class weights inversely proportional to class frequencies, we penalize misclassifications on minority classes more severely, ensuring balanced performance across all diseases."*
