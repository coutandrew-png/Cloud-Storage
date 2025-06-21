# Flask LAN Cloud Drive / Flask 局域网云盘

*A lightweight cloud drive web application built with Flask, designed to run within a local area network (LAN).*

*一个基于 Flask 构建的轻量级局域网云盘系统，适合用于局域网内的文件共享和管理。*

---

## ✨ Features / 功能特点

- User registration and login / 用户注册与登录
- Personal file upload, download, and sharing / 个人文件上传、下载、分享
- Public cloud area / 公共云盘文件区域
- Admin dashboard with logs / 管理员日志与用户文件总览
- File transfer between users / 用户之间的文件发送功能
- Password change and account deletion / 密码修改与账号删除
- SQLite-based lightweight storage / 使用 SQLite 存储
- Real-time LAN speed display / 局域网内实时网速检测显示

---

## 📦 Installation / 安装方法

1. Clone the repository / 克隆仓库:
   ```bash
   git clone https://github.com/yourusername/cloud-drive-lan.git
   cd cloud-drive-lan
   ```

2. Create a virtual environment (recommended) / 创建虚拟环境（推荐）:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows / 适用于 Windows
   ```

3. Install dependencies / 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Usage / 使用方法

Run the app locally within your LAN / 在局域网中运行：

```bash
python 1-云盘.py
```

Then visit `http://<your-ip>:5000` from any LAN device.  
然后在局域网其他设备访问 `http://<你的IP>:5000`。

**Admin note / 管理员说明**:
- You can register an account named `admin` to access the admin dashboard.  
  注册一个名为 `admin` 的账户将获得管理员权限。

---

## 📁 File Structure / 文件结构说明

- User files are stored in `uploads/用户名/`  
  用户文件存储于 `uploads/用户名/`
- Public uploads go to `uploads/public/`  
  公共上传文件存储于 `uploads/public/`
- Static files for network speed test go in `static/`  
  网络测速静态资源存储于 `static/`

---

## 🔐 Security Notes / 安全提示

- This app is intended for **trusted local environments only**.  
  本项目仅适用于 **可信的局域网环境**。
- No HTTPS or advanced authentication is implemented.  
  默认未启用 HTTPS 或高级认证机制。
- Do not expose it to the public internet without protection.  
  切勿直接部署在公网，需额外配置安全措施（如 Nginx、认证机制等）。

---

## 📄 License / 许可证

This project is licensed under the MIT License.  
本项目采用 MIT 开源许可证。  
See [LICENSE](LICENSE) for details.
