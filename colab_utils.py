import os
import yaml
import shutil
import zipfile

def prepare_for_colab():
    print("Preparing dataset for Google Colab...")
    
    base_dir = "data/archive"
    output_zip = "colab_dataset.zip"
    colab_yaml_path = os.path.join(base_dir, "data_colab.yaml")
    
    # 1. Create a Colab-friendly YAML
    # We read the existing one to get class names
    existing_yaml = os.path.join(base_dir, "data.yaml")
    with open(existing_yaml, 'r') as f:
        config = yaml.safe_load(f)
        
    # Update paths for Colab (assuming we unzip to /content/dataset)
    # Using relative paths is safest if we keep the structure
    config['train'] = "./train/images"
    config['val']   = "./valid/images"
    config['test']  = "./test/images"
    
    # Save this new config
    with open(colab_yaml_path, 'w') as f:
        yaml.dump(config, f)
    print(f"Created {colab_yaml_path}")
    
    # 2. Zip Everything
    # We need to zip: train, valid, test, and data_colab.yaml
    print(f"Zipping files to {output_zip}...")
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the YAML
        zipf.write(colab_yaml_path, arcname="data.yaml")
        
        # Add Directories
        for split in ['train', 'valid', 'test']:
            split_path = os.path.join(base_dir, split)
            if os.path.exists(split_path):
                for root, dirs, files in os.walk(split_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # We want the archive to have 'train/images/img1.jpg'
                        # arcname should be relative to base_dir
                        try:
                            arcname = os.path.relpath(file_path, base_dir)
                            zipf.write(file_path, arcname=arcname)
                        except Exception as e:
                            print(f"Skipping {file}: {e}")
            else:
                print(f"Warning: {split} folder not found in {base_dir}")

    print("Done zipping!")
    
    # 3. SPLIT the file into 500MB chunks for easier upload
    CHUNK_SIZE = 500 * 1024 * 1024 # 500 MB
    
    print(f"Splitting {output_zip} into 500MB chunks...")
    with open(output_zip, 'rb') as f:
        part_num = 1
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            
            part_name = f"{output_zip}.{part_num:03d}"
            with open(part_name, 'wb') as p:
                p.write(chunk)
            print(f"Created {part_name}")
            part_num += 1
            
    print("\n[SUCCESS] Split complete.")
    print("Please upload the .001, .002, etc. files to Google Drive/Colab.")
    print("In Colab, rejoin them with:")
    print(f"!cat {output_zip}.* > {output_zip}")
    print(f"!unzip {output_zip} -d /content/dataset")

if __name__ == "__main__":
    prepare_for_colab()
