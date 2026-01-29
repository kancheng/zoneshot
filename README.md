# ZoneShot

自訂區域截圖工具：先用 GUI 拖曳設定螢幕截圖區域，之後按鍵盤熱鍵即可自動截圖該區域。以 PyQt5 撰寫，可打包成單一 exe 獨立執行。

---

## 功能特色

| 功能 | 說明 |
|------|------|
| **拖曳設定區域** | 按「拖曳設定截圖區域」後，螢幕出現半透明覆蓋，用滑鼠拖曳畫出矩形，放開即完成設定。 |
| **熱鍵截圖** | 可選 F8～F12 作為熱鍵，程式縮到背景時也可觸發截圖。 |
| **自訂儲存位置** | 可選擇截圖儲存資料夾，預設為「我的圖片」。 |
| **單一 exe 發佈** | 可用 PyInstaller 打包成單一 exe，無需安裝 Python 即可在任意 Windows 電腦執行。 |

---

## 環境需求

- **Python** 3.7 以上  
- **作業系統**：Windows（熱鍵與截圖以 Windows 為準）

---

## 安裝與執行

### 1. 取得專案

```bash
git clone https://github.com/kancheng/zoneshot.git
cd zoneshot
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 執行程式

```bash
python main.py
```

---

## 使用方式

1. **設定截圖區域**  
   點擊「拖曳設定截圖區域」→ 主視窗會暫時隱藏，螢幕出現半透明覆蓋與說明文字 → 按住滑鼠左鍵拖曳畫出矩形 → 放開即完成設定。

2. **選擇熱鍵**  
   在下拉選單中選擇 F8～F12 其中一個作為截圖熱鍵。

3. **選擇儲存資料夾**  
   點擊「選擇資料夾」指定截圖儲存位置（預設為「我的圖片」）。

4. **截圖**  
   之後隨時按下設定的熱鍵，即會對已設定的區域截圖並儲存為 PNG（檔名格式：`screenshot_YYYYMMDD_HHMMSS.png`）。程式在背景時也可觸發。

---

## 打包成單一 exe（獨立應用程式）

可將專案打包成單一 `ZoneShot.exe`，複製到任何 Windows 電腦即可執行，無需安裝 Python。

### 方法一：使用批次檔（推薦）

在 **命令提示字元** 或 **PowerShell** 中執行（建議不要從 IDE 內建終端執行，以減少「存取被拒」錯誤）：

```bash
cd zoneshot
build_exe.bat
```

### 方法二：手動執行

```bash
cd zoneshot
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm build_exe.spec
```

完成後，可執行檔位於：

```
dist/ZoneShot.exe
```

> **若出現「存取被拒」(WinError 5)**：請在一般命令列視窗執行上述指令，或暫時將專案資料夾排除於防毒即時掃描之外。

---

## 專案結構

```
zoneshot/
├── main.py           # 主程式（PyQt5 GUI + 區域選擇 + 熱鍵截圖）
├── requirements.txt  # Python 依賴
├── build_exe.spec    # PyInstaller 打包設定（單一 exe）
├── build_exe.bat     # Windows 一鍵打包腳本
└── README.md         # 本說明文件
```

---

## 依賴套件

| 套件 | 用途 |
|------|------|
| PyQt5 | GUI 介面與視窗 |
| pynput | 全域鍵盤熱鍵監聽 |
| Pillow | 螢幕截圖 (ImageGrab) |

