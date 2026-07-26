# ManualPPT 技術棧與架構設計說明書

## 1. 系統架構概觀

ManualPPT 是一套結合 **本機瀏覽器錄製**、**流程模型建構**、**受治理自動化執行**、**證據管理** 與 **多版本 PowerPoint 手冊發布** 的系統。

系統劃分為三大平面：

```
[ Chrome/Edge Extension ]  <--->  [ Tauri Desktop App (React + TS) ]  <--->  [ FastAPI Sidecar Service ]  --->  [ Output ]
  - DOM 語意擷取                     - 桌面控制台與流程圖導覽                   - 流程模型與版本控制                     - PPTX (python-pptx)
  - 互動事件錄製                     - 錄製/人工接管切換                       - 治理授權與二次確認                     - 審核與發布報告
  - 擷取源頭敏感資訊遮罩               - 跨進程訊息通訊                         - 持久化與 checkpoint (SQLite/SQLAlchemy)
                                                                            - 證據與稽核日誌 (Append-only Audit)
```

---

## 2. 技術棧選型 (Technology Stack)

### 2.1 桌面程式平面 (Desktop App Plane)
* **桌面應用框架**：**Tauri**（輕量化本機桌面視窗與 Native API 整合）
* **UI 框架與型別**：**React + TypeScript**（極簡現代化控制台，包含流程圖與步驟表雙向編輯介面）

### 2.2 本機 Sidecar 服務平面 (Local Sidecar Service Plane)
* **運行機制**：FastAPI 作為 Tauri 的本機 Sidecar Process（以 HTTP / WebSocket 進行本機 IPC 溝通）
* **語言與運行環境**：Python 3.10+
* **環境與套件管理**：`uv` (搭配 `.venv` 虛擬環境)
* **Web 框架**：FastAPI + Uvicorn (非同步 RESTful API)
* **資料驗證與 Schema**：Pydantic v2
* **持久化與 ORM**：SQLAlchemy 2.0 + SQLite (支援 ACID、檢查點與可還原資料庫遷移)
* **簡報生成引擎**：`python-pptx` (簡報範本解析、頁面佈局、圖片與註記放置)
* **文件解析**：`pypdf` (PDF 匯入)、`python-docx` (Word 匯入)
* **測試與自動化驗證**：`pytest`、`pytest-asyncio`、`playwright`

### 2.3 瀏覽器擷取平面 (Extension Capture Plane)
* **核心框架**：Chrome / Edge Extension (Manifest V3)
  * **Content Script**：語意 DOM 擷取、Accessibility Role 辨識、與使用者互動攔截
  * **Service Worker**：事件佇列、本機白名單檢查、本機端初級遮罩

---

## 3. 核心設計原則

1. **零信任與邊界防禦**：永遠不信任瀏覽器傳回的未經校驗內容，寫入動作必須通過服務層治理檢查。
2. **本機優先 (Local-First)**：原始擷取、畫面處理、敏感欄位遮罩均在本機端或核准的本機 Sidecar 服務完成，嚴禁將未遮罩畫面傳送至第三方。
3. **單一正規化流程模型 (Canonical Workflow Model)**：探索、自動化執行與手邊操作皆歸一為版本化的流程模型 (Project, Scope, WorkflowVersion, State, Step, Branch, Checkpoint)。
4. **追溯性 (Traceability)**：每個步驟均附帶 Trace ID、Idempotency Key、原始證據索引 (Evidence ID) 及來源規格引用 (Source Reference)。
