import time

# Durdurma sinyali olarak kullanılacak bir kontrol listesi
should_run = [True, True, True]

def process_source(index):
    while should_run[index]:
        print(f"Kaynak {index} işleniyor...")
        time.sleep(1)  # Gerçek iş burada olur (video işleme vs.)
