from ultralytics import YOLO
import os
import yaml

def train_model():
    # 1. Setup paths
    dataset_yaml = os.path.abspath("data/archive/data.yaml")
    
    # Ensure the yaml exists
    if not os.path.exists(dataset_yaml):
        print(f"Error: {dataset_yaml} not found!")
        return

    # 2. Fix paths in data.yaml if necessary (Roboflow often uses relative paths that might break)
    # Let's read it first
    with open(dataset_yaml, 'r') as f:
        data_config = yaml.safe_load(f)
        
    print(f"Dataset Config: {data_config}")
    
    # Check if 'train' path is correct relative to current dir
    # If it's just 'train' or '../train', simple YOLO execution might miss it if CWD is different.
    # Best practice: Update yaml to use absolute paths momentarily or ensure CWD is correct.
    # For now, we assume CWD is project root.
    
    # 3. Initialize Model
    # Start with 'yolov8n.pt' (Nano) for speed as per requirements
    model = YOLO('yolov8n.pt') 

    # 4. Train
    print("Starting training...")
    try:
        results = model.train(
            data=dataset_yaml,
            epochs=20,          # Start with 20 epochs for quick results
            imgsz=640,
            batch=16,
            project='runs/train',
            name='ppe_model',
            single_cls=False,    # We likely have multiple classes (Helmet, Vest, etc)
            device='cpu'         # Or 0 for GPU if available. 'cpu' is safe default.
        )
        print("Training complete!")
        print(f"Best model saved at: {results.save_dir}/weights/best.pt")
        
    except Exception as e:
        print(f"Training failed: {e}")

if __name__ == "__main__":
    train_model()
