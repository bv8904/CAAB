import os
import shutil
import pandas as pd
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
import config

SOURCE_DATA_DIR = os.path.join(config.BASE_DIR, "UTKFace")
ORGANIZED_DATA_DIR = os.path.join(config.BASE_DIR, "organized_data")

def prepare_data():
    """Organizes UTKFace dataset into train/val directories for keras."""
    if not os.path.exists(SOURCE_DATA_DIR):
        print(f"Error: Dataset not found at {SOURCE_DATA_DIR}")
        return False
        
    print("Preparing data...")
    data = []
    for filename in os.listdir(SOURCE_DATA_DIR):
        if filename.endswith(".jpg"):
            try:
                # UTKFace format: [age]_[gender]_[race]_[date].jpg
                age = int(filename.split('_')[0])
                # 0-17 is child (0), 18+ is adult (1)
                label = 'child' if age < 18 else 'adult'
                data.append({'filename': filename, 'label': label})
            except (IndexError, ValueError):
                continue

    df = pd.DataFrame(data)
    train_df, val_df = train_test_split(df, test_size=0.2, stratify=df['label'], random_state=42)

    # Create directory structure
    for split, split_df in [('train', train_df), ('val', val_df)]:
        for label in ['child', 'adult']:
            os.makedirs(os.path.join(ORGANIZED_DATA_DIR, split, label), exist_ok=True)
            
        # Optional: Limit images to speed up local training (uncomment below for fast test)
        # split_df = split_df.sample(n=min(len(split_df), 1000), random_state=42)
        
        # Copy files
        print(f"Copying {len(split_df)} images to {split} directory...")
        for _, row in split_df.iterrows():
            src = os.path.join(SOURCE_DATA_DIR, row['filename'])
            dst = os.path.join(ORGANIZED_DATA_DIR, split, row['label'], row['filename'])
            if not os.path.exists(dst):
                shutil.copy(src, dst)
                
    print("Data preparation complete.")
    return True

def build_model():
    """Creates a MobileNetV2 based architecture."""
    # Use standard 224x224 input
    base_model = MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    
    # Freeze base model layers initially
    base_model.trainable = False
    
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.3)(x)  # Dropout to prevent overfitting
    
    # Output layer (Binary Classification: Child vs Adult)
    outputs = Dense(1, activation='sigmoid')(x)
    
    model = Model(inputs=base_model.input, outputs=outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), 
                  loss='binary_crossentropy', 
                  metrics=['accuracy'])
    return model

def train():
    if not prepare_data():
        return
        
    print("Building model...")
    model = build_model()
    
    # 1/255 rescaling to match ml_engine preprocessing
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True
    )
    
    val_datagen = ImageDataGenerator(rescale=1./255)
    
    train_generator = train_datagen.flow_from_directory(
        os.path.join(ORGANIZED_DATA_DIR, "train"),
        target_size=config.FRAME_SIZE,
        batch_size=32,
        class_mode='binary'
    )
    
    val_generator = val_datagen.flow_from_directory(
        os.path.join(ORGANIZED_DATA_DIR, "val"),
        target_size=config.FRAME_SIZE,
        batch_size=32,
        class_mode='binary'
    )
    
    print(f"Class indices: {train_generator.class_indices}")
    # We want 'child' to be 0, and 'adult' to be 1 to match ml_engine logic.
    # ImageDataGenerator sorts alphanumerically, so 'adult' is 0, 'child' is 1!
    # THIS is critical. Let's force classes so child is 0, adult is 1.
    
    train_generator = train_datagen.flow_from_directory(
        os.path.join(ORGANIZED_DATA_DIR, "train"),
        target_size=config.FRAME_SIZE,
        batch_size=32,
        classes=['child', 'adult'], # ENFORCE ORDER
        class_mode='binary'
    )
    
    val_generator = val_datagen.flow_from_directory(
        os.path.join(ORGANIZED_DATA_DIR, "val"),
        target_size=config.FRAME_SIZE,
        batch_size=32,
        classes=['child', 'adult'], # ENFORCE ORDER
        class_mode='binary'
    )
    
    print(f"Corrected Class indices (Child=0, Adult=1): {train_generator.class_indices}")

    # Callbacks
    os.makedirs(os.path.dirname(config.MODEL_PATH), exist_ok=True)
    checkpoint = ModelCheckpoint(config.MODEL_PATH, monitor='val_accuracy', save_best_only=True, mode='max', verbose=1)
    early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=2, min_lr=0.00001)

    print("Starting training (Phase 1: Head Only)...")
    model.fit(
        train_generator,
        epochs=5,
        validation_data=val_generator,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )
    print(f"Training complete. Model saved to {config.MODEL_PATH}")

if __name__ == "__main__":
    train()
