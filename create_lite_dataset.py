import os
import shutil
import zipfile
import random
import yaml

def create_lite_dataset(source_dir="data/archive", output_zip="colab_dataset_lite.zip", subset_ratio=0.05):
    """
    Creates a lite version of the dataset by sampling a subset of images.
    subset_ratio: 0.05 means 5% of the data (approx 2000 images if total is 40k).
    """
    print(f"Creating Lite Dataset from {source_dir} with ratio {subset_ratio}...")
    
    # Paths
    colab_yaml_path = "data_colab_lite.yaml"
    
    # 1. Create Lite YAML
    original_yaml = os.path.join(source_dir, "data.yaml")
    if not os.path.exists(original_yaml):
        print("Error: data.yaml not found at", original_yaml)
        return

    with open(original_yaml, 'r') as f:
        config = yaml.safe_load(f)
        
    # Update paths to be relative for Colab
    config['train'] = "./train/images"
    config['val']   = "./valid/images"
    config['test']  = "./test/images"
    
    with open(colab_yaml_path, 'w') as f:
        yaml.dump(config, f)
        
    # 2. Zip Subset
    count = 0
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add YAML
        zipf.write(colab_yaml_path, arcname="data.yaml")
        
        # Walk and sample
        for split in ['train', 'valid', 'test']:
            split_path = os.path.join(source_dir, split)
            if not os.path.exists(split_path):
                continue
                
            print(f"Processing {split}...")
            
            # We need to pair images with labels
            # Assuming structure: split/images/img.jpg and split/labels/img.txt
            image_dir = os.path.join(split_path, "images")
            label_dir = os.path.join(split_path, "labels")
            
            if not os.path.exists(image_dir):
                print(f"Skipping {split} - no images folder")
                continue
                
            all_images = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            # Select subset
            # For validation/test, we might want to keep more, but for "Lite" let's just sample everything
            k = int(len(all_images) * subset_ratio)
            # Ensure at least some images if available
            k = max(10, k) if len(all_images) > 0 else 0
            k = min(k, len(all_images))
            
            selected_images = random.sample(all_images, k)
            
            for img_name in selected_images:
                # Add Image
                src_img = os.path.join(image_dir, img_name)
                arc_img = os.path.join(split, "images", img_name)
                zipf.write(src_img, arcname=arc_img)
                
                # Add Label
                label_name = os.path.splitext(img_name)[0] + ".txt"
                src_label = os.path.join(label_dir, label_name)
                arc_label = os.path.join(split, "labels", label_name)
                
                if os.path.exists(src_label):
                    zipf.write(src_label, arcname=arc_label)
                
                count += 1
                
    print(f"Done! Created {output_zip} with {count} samples.")
    print(f"Size: {os.path.getsize(output_zip) / (1024*1024):.2f} MB")
    
    # Cleanup temp yaml
    if os.path.exists(colab_yaml_path):
        os.remove(colab_yaml_path)

if __name__ == "__main__":
    # Adjust ratio to target ~100-200MB
    # 44k images * 0.02 = ~880 pairs
    create_lite_dataset(subset_ratio=0.02)
