"""
Web Dashboard for Discord Bot 

Simple web interface for bot setup and monitoring
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import urllib.parse
from datetime import datetime
from bot.watermark import WatermarkProcessor
from bot.user_manager import UserManager
from bot.logger import BotLogger

class DashboardHandler(BaseHTTPRequestHandler):
    watermark_processor = None
    user_manager = None
    logger = None
    
    @classmethod
    def initialize_components(cls):
        if cls.watermark_processor is None:
            cls.watermark_processor = WatermarkProcessor()
        if cls.user_manager is None:
            cls.user_manager = UserManager()
        if cls.logger is None:
            cls.logger = BotLogger()
    
    def __init__(self, *args, **kwargs):
        self.initialize_components()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/dashboard' or self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/stats':
            self.serve_stats()
        elif self.path == '/api/files':
            self.serve_files()
        elif self.path == '/api/logs':
            self.serve_logs()
        elif self.path == '/api/analytics':
            self.serve_analytics()
        elif self.path == '/api/users':
            self.serve_users()
        elif self.path == '/api/activity':
            self.serve_activity()
        elif self.path.startswith('/api/file/'):
            self.serve_file_details()
        elif self.path == '/api/reveals':
            self.serve_reveals()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/api/delete':
            self.handle_delete()
        elif self.path == '/api/add-admin':
            self.handle_add_admin()
        elif self.path == '/api/remove-admin':
            self.handle_remove_admin()
        elif self.path == '/api/bulk-delete':
            self.handle_bulk_delete()
        elif self.path == '/api/export':
            self.handle_export()
        elif self.path == '/api/watermark':
            self.handle_watermark_upload()
        elif self.path == '/api/watermark-settings':
            self.handle_watermark_settings()
        else:
            self.send_error(404)

    def serve_dashboard(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Advanced Discord Bot Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@100;200;300;400;500;600;700;800;900&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            color: #1d1d1f;
            line-height: 1.6;
            overflow-x: hidden;
            min-height: 100vh;
        }
        
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 280px;
            height: 100vh;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 30px 20px;
            border-right: 1px solid rgba(255, 255, 255, 0.3);
            overflow-y: auto;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .sidebar h2 {
            background: linear-gradient(45deg, #FF6B35, #F7931E);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 40px;
            text-align: center;
            font-size: 1.8em;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .nav-item {
            padding: 16px 20px;
            margin: 6px 0;
            border-radius: 16px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 500;
            color: #1d1d1f;
            position: relative;
            overflow: hidden;
        }
        
        .nav-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, #FF6B35, #F7931E);
            opacity: 0;
            transition: opacity 0.3s ease;
            border-radius: 16px;
        }
        
        .nav-item:hover::before { opacity: 0.1; }
        .nav-item.active::before { opacity: 1; }
        .nav-item.active { color: white; font-weight: 600; }
        .nav-item span { position: relative; z-index: 1; }
        
        .main-content {
            margin-left: 280px;
            padding: 30px;
            min-height: 100vh;
        }
        
        .header { 
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .header h1 { 
            background: linear-gradient(45deg, #FF6B35, #F7931E);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.5em;
            font-weight: 800;
            letter-spacing: -1px;
        }
        
        .header-actions {
            display: flex;
            gap: 12px;
        }
        
        .content-section {
            display: none;
            animation: fadeIn 0.5s ease-in-out;
        }
        
        .content-section.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .cards { 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .card { 
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 30px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #007AFF, #5856D6, #AF52DE);
            border-radius: 20px 20px 0 0;
        }
        
        .card:hover { 
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        }
        
        .card h3 { 
            background: linear-gradient(45deg, #007AFF, #5856D6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
            font-weight: 700;
            font-size: 1.3em;
        }
        
        .chart-container {
            position: relative;
            height: 320px;
            margin: 25px 0;
            border-radius: 16px;
            overflow: hidden;
        }
        
        .wide-card {
            grid-column: 1 / -1;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .stat-box {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 25px 20px;
            border-radius: 18px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-box::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #007AFF, #5856D6);
        }
        
        .stat-box:hover {
            transform: translateY(-4px);
        }
        
        .stat-number { 
            font-size: 2.5em; 
            font-weight: 800; 
            background: linear-gradient(45deg, #007AFF, #5856D6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }
        
        .stat-label { 
            font-size: 0.95em; 
            color: #6e6e73;
            font-weight: 500;
        }
        
        .file-list {
            max-height: 350px;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        
        .file-item {
            padding: 18px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s ease;
        }
        
        .file-item:last-child { border-bottom: none; }
        .file-item:hover { background: rgba(255, 255, 255, 0.4); }
        .file-name { font-weight: 600; color: #1d1d1f; }
        .file-id { 
            font-family: 'SF Mono', Monaco, monospace; 
            color: #8e8e93; 
            font-size: 0.9em;
            font-weight: 500;
        }
        .delete-btn {
            background: linear-gradient(45deg, #FF3B30, #FF9500);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 0.85em;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(255, 59, 48, 0.3);
        }
        .delete-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 59, 48, 0.4);
        }
        
        .logs {
            max-height: 400px;
            overflow-y: auto;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 20px;
            border-radius: 16px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.9em;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }
        .log-entry {
            margin-bottom: 12px;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 12px;
            border-left: 4px solid #007AFF;
            transition: background 0.2s ease;
        }
        .log-entry:hover { background: rgba(255, 255, 255, 0.9); }
        .log-time { color: #8e8e93; font-weight: 500; }
        .log-action { 
            color: #007AFF; 
            font-weight: 700;
            background: linear-gradient(45deg, #007AFF, #5856D6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #1d1d1f;
            font-weight: 600;
            font-size: 0.95em;
        }
        .form-group input {
            width: 100%;
            padding: 16px 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.9);
            color: #1d1d1f;
            font-size: 1em;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        .form-group input:focus {
            outline: none;
            border-color: #007AFF;
            box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1);
            transform: translateY(-2px);
        }
        .btn {
            background: linear-gradient(45deg, #007AFF, #5856D6);
            color: white;
            border: none;
            padding: 16px 32px;
            border-radius: 16px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            box-shadow: 0 4px 20px rgba(0, 122, 255, 0.3);
            letter-spacing: 0.5px;
        }
        .btn:hover { 
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 30px rgba(0, 122, 255, 0.4);
        }
        .btn:active {
            transform: translateY(-1px) scale(0.98);
        }
        
        .status {
            padding: 16px 20px;
            border-radius: 16px;
            margin: 15px 0;
            font-weight: 600;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }
        .status.success { 
            background: linear-gradient(45deg, #34C759, #30D158);
            color: white;
        }
        .status.error { 
            background: linear-gradient(45deg, #FF3B30, #FF6B6B);
            color: white;
        }
        
        .refresh-btn, .action-btn {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            color: #1d1d1f;
            border: 2px solid rgba(0, 122, 255, 0.3);
            padding: 12px 20px;
            border-radius: 14px;
            cursor: pointer;
            margin: 0 8px;
            font-size: 0.9em;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }
        .refresh-btn:hover, .action-btn:hover { 
            background: linear-gradient(45deg, #007AFF, #5856D6);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(0, 122, 255, 0.3);
        }
        .danger-btn {
            background: linear-gradient(45deg, #FF3B30, #FF9500);
            border-color: rgba(255, 59, 48, 0.3);
            color: white;
        }
        .danger-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(255, 59, 48, 0.4);
        }
        .success-btn {
            background: linear-gradient(45deg, #34C759, #30D158);
            border-color: rgba(52, 199, 89, 0.3);
            color: white;
        }
        .success-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(52, 199, 89, 0.4);
        }
        .table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 25px 0;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        .table th, .table td {
            padding: 18px 20px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.3);
        }
        .table th {
            background: linear-gradient(45deg, #007AFF, #5856D6);
            color: white;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .table tr:hover {
            background: rgba(0, 122, 255, 0.05);
        }
        .checkbox {
            margin-right: 12px;
            transform: scale(1.2);
        }
        .search-bar {
            width: 100%;
            max-width: 400px;
            padding: 16px 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            color: #1d1d1f;
            font-size: 1em;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }
        .search-bar:focus {
            outline: none;
            border-color: #007AFF;
            box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1);
            transform: translateY(-2px);
            margin-bottom: 20px;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        .modal-content {
            background-color: #36393f;
            margin: 15% auto;
            padding: 20px;
            border-radius: 10px;
            width: 80%;
            max-width: 500px;
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover { color: #fff; }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #40444b;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: #5865f2;
            transition: width 0.3s;
        }
        .tag {
            display: inline-block;
            background: #5865f2;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
        }
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .alert-info { background: #3ba55c; }
        .alert-warning { background: #faa61a; }
        .alert-error { background: #ed4245; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>Bot Dashboard</h2>
        <div class="nav-item active" onclick="showSection('overview')">
            📊 Overview
        </div>
        <div class="nav-item" onclick="showSection('analytics')">
            📈 Analytics
        </div>
        <div class="nav-item" onclick="showSection('files')">
            📁 Files
        </div>
        <div class="nav-item" onclick="showSection('users')">
            👥 Users
        </div>
        <div class="nav-item" onclick="showSection('activity')">
            📝 Activity
        </div>
        <div class="nav-item" onclick="showSection('settings')">
            ⚙️ Settings
        </div>
    </div>

    <div class="main-content">
        <div class="header">
            <h1 id="pageTitle">Overview</h1>
            <div class="header-actions">
                <button class="action-btn" onclick="exportData()">📤 Export</button>
                <button class="action-btn" onclick="refreshAll()">🔄 Refresh</button>
            </div>
        </div>

        <!-- Overview Section -->
        <div id="overview" class="content-section active">
            <div class="cards">
                <div class="card">
                    <h3>📊 Quick Stats</h3>
                    <div class="stats-grid">
                        <div class="stat-box">
                            <div class="stat-number" id="totalFiles">-</div>
                            <div class="stat-label">Total Files</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="totalAdmins">-</div>
                            <div class="stat-label">Admins</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="totalLogs">-</div>
                            <div class="stat-label">Activities</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="todayUploads">-</div>
                            <div class="stat-label">Today</div>
                        </div>
                    </div>
                </div>
                
                <div class="card wide-card">
                    <h3>📈 Activity Overview</h3>
                    <div class="chart-container">
                        <canvas id="activityChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Watermarks Section -->
        <div id="watermarks" class="content-section">
            <div class="cards">
                <div class="card">
                    <h3>🎯 Watermark Generator</h3>
                    <form id="watermarkForm" onsubmit="generateWatermark(event)">
                        <div class="form-group">
                            <label>Upload File:</label>
                            <input type="file" id="fileInput" accept="image/*,video/*" required>
                        </div>
                        <div class="form-group">
                            <label>Description:</label>
                            <input type="text" id="descInput" placeholder="Brief description..." required>
                        </div>
                        <button type="submit" class="btn">Generate Watermark</button>
                    </form>
                    <div id="watermarkStatus"></div>
                </div>
                
                <div class="card">
                    <h3>🔧 Watermark Settings</h3>
                    <div class="form-group">
                        <label>Font Size:</label>
                        <input type="range" id="fontSize" min="20" max="100" value="40">
                        <span id="fontSizeValue">40px</span>
                    </div>
                    <div class="form-group">
                        <label>Opacity:</label>
                        <input type="range" id="opacity" min="50" max="255" value="150">
                        <span id="opacityValue">150</span>
                    </div>
                    <div class="form-group">
                        <label>Grid Density:</label>
                        <select id="gridDensity">
                            <option value="low">Low (8x10)</option>
                            <option value="medium" selected>Medium (12x15)</option>
                            <option value="high">High (16x20)</option>
                        </select>
                    </div>
                    <button onclick="updateWatermarkSettings()" class="btn">Update Settings</button>
                </div>
            </div>
        </div>

        <!-- Reveals Section -->
        <div id="reveals" class="content-section">
            <div class="cards">
                <div class="card">
                    <h3>🔥 Active Reveals</h3>
                    <div id="activeReveals">Loading reveals...</div>
                </div>
                
                <div class="card">
                    <h3>📊 Reveal Statistics</h3>
                    <div id="revealStats">
                        <div class="stat-item">
                            <span class="stat-label">Total Reveals:</span>
                            <span class="stat-value" id="totalReveals">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Active Today:</span>
                            <span class="stat-value" id="todayReveals">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Most Popular:</span>
                            <span class="stat-value" id="popularContent">N/A</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Analytics Section -->
        <div id="analytics" class="content-section">
            <div class="cards">
                <div class="card">
                    <h3>📈 Upload Trends</h3>
                    <div class="chart-container">
                        <canvas id="uploadsChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h3>👥 User Activity</h3>
                    <div class="chart-container">
                        <canvas id="usersChart"></canvas>
                    </div>
                </div>
                
                <div class="card wide-card">
                    <h3>🔍 Detailed Analytics</h3>
                    <div id="detailedAnalytics">Loading analytics...</div>
                </div>
            </div>
        </div>

        <!-- Files Section -->
        <div id="files" class="content-section">
            <div class="card">
                <h3>📁 File Management</h3>
                <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 20px;">
                    <input type="text" id="fileSearch" class="search-bar" placeholder="Search files..." onkeyup="filterFiles()">
                    <div>
                        <button class="action-btn" onclick="selectAllFiles()">Select All</button>
                        <button class="danger-btn" onclick="bulkDeleteFiles()">Delete Selected</button>
                    </div>
                </div>
                <div id="filesTable">Loading files...</div>
            </div>
        </div>

        <!-- Users Section -->
        <div id="users" class="content-section">
            <div class="cards">
                <div class="card">
                    <h3>👥 Admin Management</h3>
                    <form onsubmit="addAdmin(event)">
                        <div class="form-group">
                            <label>Add Admin (User ID or @mention):</label>
                            <input type="text" id="adminInput" placeholder="123456789012345678 or @username" required>
                        </div>
                        <button type="submit" class="btn">Add Admin</button>
                    </form>
                    <div id="adminStatus"></div>
                </div>
                
                <div class="card">
                    <h3>Current Admins</h3>
                    <div id="adminsList">Loading admins...</div>
                </div>
            </div>
        </div>

        <!-- Activity Section -->
        <div id="activity" class="content-section">
            <div class="card">
                <h3>📝 Activity Monitor</h3>
                <input type="text" id="logSearch" class="search-bar" placeholder="Search activity..." onkeyup="filterLogs()">
                <div id="activityTable">Loading activity...</div>
            </div>
        </div>

        <!-- Settings Section -->
        <div id="settings" class="content-section">
            <div class="cards">
                <div class="card">
                    <h3>⚙️ Bot Configuration</h3>
                    <div id="botSettings">
                        <p><strong>Status:</strong> <span class="tag">Online</span></p>
                        <p><strong>Uptime:</strong> <span id="uptime">Calculating...</span></p>
                        <p><strong>Version:</strong> v2.0.0</p>
                        <p><strong>Dashboard Port:</strong> 5001</p>
                        <p><strong>Bot Port:</strong> 5000</p>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🛠️ System Tools</h3>
                    <button class="action-btn" onclick="clearCache()">Clear Cache</button>
                    <button class="action-btn" onclick="exportLogs()">Export Logs</button>
                    <button class="danger-btn" onclick="resetBot()">Reset Bot Data</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Modals -->
    <div id="fileModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('fileModal')">&times;</span>
            <h3 id="modalFileTitle">File Details</h3>
            <div id="modalFileContent">Loading...</div>
        </div>
    </div>

    <div id="confirmModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('confirmModal')">&times;</span>
            <h3>Confirm Action</h3>
            <p id="confirmMessage">Are you sure?</p>
            <div style="margin-top: 20px;">
                <button class="btn" onclick="confirmAction()">Yes</button>
                <button class="action-btn" onclick="closeModal('confirmModal')">Cancel</button>
            </div>
        </div>
    </div>

    <script>
        function loadStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalFiles').textContent = data.totalFiles;
                    document.getElementById('totalAdmins').textContent = data.totalAdmins;
                    document.getElementById('totalLogs').textContent = data.totalLogs;
                })
                .catch(error => console.error('Error loading stats:', error));
        }

        function loadFiles() {
            fetch('/api/files')
                .then(response => response.json())
                .then(data => {
                    const filesDiv = document.getElementById('files');
                    if (data.files.length === 0) {
                        filesDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #b9bbbe;">No files uploaded yet</div>';
                        return;
                    }
                    
                    filesDiv.innerHTML = data.files.map(file => `
                        <div class="file-item">
                            <div>
                                <div class="file-name">${file.filename}</div>
                                <div class="file-id">${file.watermark_id} • ${file.date}</div>
                            </div>
                            <button class="delete-btn" onclick="deleteFile('${file.watermark_id}')">Delete</button>
                        </div>
                    `).join('');
                })
                .catch(error => console.error('Error loading files:', error));
        }

        function loadLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const logsDiv = document.getElementById('logs');
                    if (data.logs.length === 0) {
                        logsDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #b9bbbe;">No activity yet</div>';
                        return;
                    }
                    
                    logsDiv.innerHTML = data.logs.map(log => `
                        <div class="log-entry">
                            <span class="log-time">[${log.time}]</span>
                            <span class="log-action">${log.action}</span>
                            - ${log.details}
                        </div>
                    `).join('');
                })
                .catch(error => console.error('Error loading logs:', error));
        }

        function deleteFile(watermarkId) {
            if (!confirm('Are you sure you want to delete this file?')) return;
            
            fetch('/api/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ watermark_id: watermarkId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadFiles();
                    loadStats();
                } else {
                    alert('Error deleting file: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error deleting file');
            });
        }

        function addAdmin(event) {
            event.preventDefault();
            const input = document.getElementById('adminInput');
            const status = document.getElementById('adminStatus');
            
            fetch('/api/add-admin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: input.value })
            })
            .then(response => response.json())
            .then(data => {
                status.innerHTML = `<div class="status ${data.success ? 'success' : 'error'}">${data.message}</div>`;
                if (data.success) {
                    input.value = '';
                    loadStats();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                status.innerHTML = '<div class="status error">Error adding admin</div>';
            });
        }

        let charts = {};
        let selectedFiles = new Set();
        let currentSection = 'overview';
        let pendingAction = null;

        function showSection(section) {
            // Hide all sections
            document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            
            // Show selected section
            document.getElementById(section).classList.add('active');
            event.target.classList.add('active');
            
            // Update page title
            const titles = {
                'overview': 'Overview',
                'analytics': 'Analytics',
                'files': 'Files',
                'users': 'Users', 
                'activity': 'Activity',
                'settings': 'Settings'
            };
            document.getElementById('pageTitle').textContent = titles[section];
            currentSection = section;
            
            // Load section data
            loadSectionData(section);
        }

        function loadSectionData(section) {
            switch(section) {
                case 'overview':
                    loadStats();
                    loadActivityChart();
                    break;
                case 'watermarks':
                    loadWatermarkSettings();
                    break;
                case 'reveals':
                    loadRevealsData();
                    break;
                case 'analytics':
                    loadAnalytics();
                    break;
                case 'files':
                    loadFilesTable();
                    break;
                case 'users':
                    loadAdminsList();
                    break;
                case 'activity':
                    loadActivityTable();
                    break;
                case 'settings':
                    loadSettings();
                    break;
            }
        }

        function loadActivityChart() {
            fetch('/api/activity')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('activityChart').getContext('2d');
                    if (charts.activity) charts.activity.destroy();
                    
                    charts.activity = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.dates,
                            datasets: [{
                                label: 'Daily Activities',
                                data: data.activities,
                                borderColor: '#007AFF',
                                backgroundColor: 'rgba(0, 122, 255, 0.1)',
                                tension: 0.4,
                                borderWidth: 3,
                                pointBackgroundColor: '#007AFF',
                                pointBorderColor: '#ffffff',
                                pointBorderWidth: 2,
                                pointRadius: 6
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false }
                            },
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                })
                .catch(error => console.error('Error loading activity chart:', error));
        }

        function loadAnalytics() {
            // Load multiple charts for analytics
            loadUploadsChart();
            loadUsersChart();
            loadDetailedAnalytics();
        }

        function loadUploadsChart() {
            fetch('/api/analytics')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('uploadsChart').getContext('2d');
                    if (charts.uploads) charts.uploads.destroy();
                    
                    charts.uploads = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.uploadDates,
                            datasets: [{
                                label: 'Uploads',
                                data: data.uploadCounts,
                                backgroundColor: 'linear-gradient(45deg, #007AFF, #5856D6)',
                                borderColor: '#007AFF',
                                borderWidth: 2,
                                borderRadius: 8
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });
                })
                .catch(error => console.error('Error loading uploads chart:', error));
        }

        function loadUsersChart() {
            fetch('/api/analytics')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('usersChart').getContext('2d');
                    if (charts.users) charts.users.destroy();
                    
                    charts.users = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: data.userLabels,
                            datasets: [{
                                data: data.userCounts,
                                backgroundColor: ['#007AFF', '#34C759', '#FF9500', '#FF3B30'],
                                borderWidth: 0,
                                hoverOffset: 8
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });
                })
                .catch(error => console.error('Error loading users chart:', error));
        }

        function loadDetailedAnalytics() {
            fetch('/api/analytics')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('detailedAnalytics');
                    container.innerHTML = `
                        <div class="stats-grid">
                            <div class="stat-box">
                                <div class="stat-number">${data.avgUploadsPerDay}</div>
                                <div class="stat-label">Avg Daily Uploads</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-number">${data.mostActiveUser}</div>
                                <div class="stat-label">Most Active User</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-number">${data.totalSize}</div>
                                <div class="stat-label">Total Storage</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-number">${data.successRate}%</div>
                                <div class="stat-label">Success Rate</div>
                            </div>
                        </div>
                    `;
                })
                .catch(error => console.error('Error loading detailed analytics:', error));
        }

        function loadFilesTable() {
            fetch('/api/files')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('filesTable');
                    if (data.files.length === 0) {
                        container.innerHTML = '<p style="text-align: center; padding: 20px;">No files uploaded yet</p>';
                        return;
                    }
                    
                    let html = '<table class="table"><thead><tr>';
                    html += '<th><input type="checkbox" onchange="toggleAllFiles()"></th>';
                    html += '<th>File Name</th><th>Watermark ID</th><th>Date</th><th>Size</th><th>Actions</th>';
                    html += '</tr></thead><tbody>';
                    
                    data.files.forEach(file => {
                        html += `<tr>
                            <td><input type="checkbox" class="file-checkbox" value="${file.watermark_id}" onchange="toggleFileSelection('${file.watermark_id}')"></td>
                            <td><strong>${file.filename}</strong><br><small>${file.description}</small></td>
                            <td><code>${file.watermark_id}</code></td>
                            <td>${file.date}</td>
                            <td>${file.size || 'Unknown'}</td>
                            <td>
                                <button class="action-btn" onclick="viewFile('${file.watermark_id}')">View</button>
                                <button class="danger-btn" onclick="deleteFile('${file.watermark_id}')">Delete</button>
                            </td>
                        </tr>`;
                    });
                    
                    html += '</tbody></table>';
                    container.innerHTML = html;
                })
                .catch(error => console.error('Error loading files:', error));
        }

        function loadAdminsList() {
            fetch('/api/users')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('adminsList');
                    if (data.admins.length === 0) {
                        container.innerHTML = '<p>No admins configured</p>';
                        return;
                    }
                    
                    let html = '<table class="table"><thead><tr><th>User ID</th><th>Added Date</th><th>Actions</th></tr></thead><tbody>';
                    data.admins.forEach(admin => {
                        html += `<tr>
                            <td><code>${admin.id}</code></td>
                            <td>${admin.added || 'Unknown'}</td>
                            <td><button class="danger-btn" onclick="removeAdmin('${admin.id}')">Remove</button></td>
                        </tr>`;
                    });
                    html += '</tbody></table>';
                    container.innerHTML = html;
                })
                .catch(error => console.error('Error loading admins:', error));
        }

        function loadActivityTable() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('activityTable');
                    if (data.logs.length === 0) {
                        container.innerHTML = '<p style="text-align: center; padding: 20px;">No activity yet</p>';
                        return;
                    }
                    
                    let html = '<table class="table"><thead><tr><th>Time</th><th>Action</th><th>Details</th></tr></thead><tbody>';
                    data.logs.forEach(log => {
                        html += `<tr>
                            <td>${log.time}</td>
                            <td><span class="tag">${log.action}</span></td>
                            <td>${log.details}</td>
                        </tr>`;
                    });
                    html += '</tbody></table>';
                    container.innerHTML = html;
                })
                .catch(error => console.error('Error loading activity:', error));
        }

        function loadSettings() {
            // Calculate uptime (placeholder)
            const startTime = new Date().getTime() - (Math.random() * 3600000); // Random uptime
            const uptime = Math.floor((new Date().getTime() - startTime) / 1000 / 60); // minutes
            document.getElementById('uptime').textContent = uptime + ' minutes';
        }

        function toggleFileSelection(id) {
            if (selectedFiles.has(id)) {
                selectedFiles.delete(id);
            } else {
                selectedFiles.add(id);
            }
        }

        function toggleAllFiles() {
            const checkboxes = document.querySelectorAll('.file-checkbox');
            const selectAll = event.target.checked;
            checkboxes.forEach(cb => {
                cb.checked = selectAll;
                if (selectAll) {
                    selectedFiles.add(cb.value);
                } else {
                    selectedFiles.delete(cb.value);
                }
            });
        }

        function selectAllFiles() {
            document.querySelectorAll('.file-checkbox').forEach(cb => {
                cb.checked = true;
                selectedFiles.add(cb.value);
            });
        }

        function bulkDeleteFiles() {
            if (selectedFiles.size === 0) {
                alert('No files selected');
                return;
            }
            showConfirmModal(`Delete ${selectedFiles.size} selected files?`, () => {
                // Implement bulk delete
                fetch('/api/bulk-delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ files: Array.from(selectedFiles) })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        selectedFiles.clear();
                        loadFilesTable();
                        showAlert('Files deleted successfully', 'success');
                    } else {
                        showAlert('Error deleting files: ' + data.error, 'error');
                    }
                });
            });
        }

        function viewFile(id) {
            fetch(`/api/file/${id}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('modalFileTitle').textContent = data.filename;
                    document.getElementById('modalFileContent').innerHTML = `
                        <p><strong>Watermark ID:</strong> ${data.watermark_id}</p>
                        <p><strong>Description:</strong> ${data.description}</p>
                        <p><strong>Upload Date:</strong> ${data.date}</p>
                        <p><strong>File Size:</strong> ${data.size}</p>
                        <p><strong>Deliveries:</strong> ${data.deliveries}</p>
                    `;
                    showModal('fileModal');
                });
        }

        function removeAdmin(id) {
            showConfirmModal(`Remove admin ${id}?`, () => {
                fetch('/api/remove-admin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: id })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadAdminsList();
                        showAlert('Admin removed successfully', 'success');
                    } else {
                        showAlert('Error removing admin: ' + data.message, 'error');
                    }
                });
            });
        }

        function showModal(id) {
            document.getElementById(id).style.display = 'block';
        }

        function closeModal(id) {
            document.getElementById(id).style.display = 'none';
        }

        function showConfirmModal(message, callback) {
            document.getElementById('confirmMessage').textContent = message;
            pendingAction = callback;
            showModal('confirmModal');
        }

        function confirmAction() {
            if (pendingAction) {
                pendingAction();
                pendingAction = null;
            }
            closeModal('confirmModal');
        }

        function showAlert(message, type) {
            // Create and show alert
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`;
            alert.textContent = message;
            document.body.appendChild(alert);
            setTimeout(() => alert.remove(), 3000);
        }

        function exportData() {
            fetch('/api/export', { method: 'POST' })
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'bot-data-export.json';
                    a.click();
                });
        }

        function refreshAll() {
            loadSectionData(currentSection);
            showAlert('Data refreshed', 'info');
        }

        function filterFiles() {
            const query = document.getElementById('fileSearch').value.toLowerCase();
            const rows = document.querySelectorAll('#filesTable tr');
            rows.forEach((row, index) => {
                if (index === 0) return; // Skip header
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        }

        function filterLogs() {
            const query = document.getElementById('logSearch').value.toLowerCase();
            const rows = document.querySelectorAll('#activityTable tr');
            rows.forEach((row, index) => {
                if (index === 0) return; // Skip header
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        }

        function generateWatermark(event) {
            event.preventDefault();
            const fileInput = document.getElementById('fileInput');
            const descInput = document.getElementById('descInput');
            const status = document.getElementById('watermarkStatus');
            
            if (!fileInput.files[0]) {
                status.innerHTML = '<div class="status error">Please select a file</div>';
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('description', descInput.value);
            
            status.innerHTML = '<div class="status info">Processing watermark...</div>';
            
            fetch('/api/watermark', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    status.innerHTML = '<div class="status success">Watermark generated successfully!</div>';
                    loadStats();
                    loadFilesTable();
                } else {
                    status.innerHTML = `<div class="status error">Error: ${data.error}</div>`;
                }
            })
            .catch(error => {
                status.innerHTML = '<div class="status error">Upload failed</div>';
            });
        }
        
        function updateWatermarkSettings() {
            const settings = {
                fontSize: document.getElementById('fontSize').value,
                opacity: document.getElementById('opacity').value,
                gridDensity: document.getElementById('gridDensity').value
            };
            
            fetch('/api/watermark-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Watermark settings updated!', 'success');
                }
            });
        }
        
        function loadWatermarkSettings() {
            const fontSize = document.getElementById('fontSize');
            const opacity = document.getElementById('opacity');
            
            fontSize.oninput = () => {
                document.getElementById('fontSizeValue').textContent = fontSize.value + 'px';
            };
            
            opacity.oninput = () => {
                document.getElementById('opacityValue').textContent = opacity.value;
            };
        }
        
        function loadRevealsData() {
            fetch('/api/reveals')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalReveals').textContent = data.total || 0;
                    document.getElementById('todayReveals').textContent = data.today || 0;
                    document.getElementById('popularContent').textContent = data.popular || 'N/A';
                    
                    const revealsDiv = document.getElementById('activeReveals');
                    if (data.active && data.active.length > 0) {
                        revealsDiv.innerHTML = data.active.map(reveal => `
                            <div class="reveal-item">
                                <strong>${reveal.filename}</strong>
                                <span>Clicks: ${reveal.clicks}</span>
                                <span>Created: ${new Date(reveal.created).toLocaleDateString()}</span>
                            </div>
                        `).join('');
                    } else {
                        revealsDiv.innerHTML = '<p>No active reveals</p>';
                    }
                });
        }
        
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 1000;
                animation: slideIn 0.3s ease;
                background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            `;
            
            document.body.appendChild(notification);
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        // Load initial data
        loadStats();
        loadSectionData('overview');

        // Auto-refresh every 30 seconds
        setInterval(() => {
            if (currentSection === 'overview') {
                loadStats();
                loadActivityChart();
            } else if (currentSection === 'reveals') {
                loadRevealsData();
            }
        }, 30000);
    </script>
</body>
</html>
        '''
        self.wfile.write(html.encode())

    def serve_stats(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        files = self.__class__.watermark_processor.get_all_processed_files()
        admins = self.__class__.user_manager.get_admins()
        logs = self.__class__.logger.get_recent_logs(100)
        
        stats = {
            'totalFiles': len(files),
            'totalAdmins': len(admins),
            'totalLogs': len(logs)
        }
        
        self.wfile.write(json.dumps(stats).encode())

    def serve_files(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        files = self.__class__.watermark_processor.get_all_processed_files()
        file_list = []
        
        for watermark_id, file_info in files.items():
            upload_date = file_info.get('created_at', 'Unknown')
            if upload_date != 'Unknown' and 'T' in upload_date:
                try:
                    dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                    upload_date = dt.strftime('%d-%m-%Y %H:%M')
                except:
                    upload_date = upload_date.split('T')[0]
            
            file_list.append({
                'watermark_id': watermark_id,
                'filename': file_info.get('original_filename', 'Unknown'),
                'date': upload_date,
                'description': file_info.get('description', 'No description')
            })
        
        # Sort by date, newest first
        file_list.sort(key=lambda x: x['date'], reverse=True)
        
        self.wfile.write(json.dumps({'files': file_list}).encode())

    def serve_logs(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        logs = self.__class__.logger.get_recent_logs(50)
        log_list = []
        
        for log in reversed(logs):  # Show newest first
            timestamp = log.get('timestamp', '')
            if timestamp and 'T' in timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp
            else:
                time_str = 'Unknown'
            
            action = log.get('action', 'unknown')
            details = ''
            
            if action == 'upload':
                details = f"File uploaded: {log.get('filename', 'Unknown')} ({log.get('watermark_id', 'No ID')})"
            elif action == 'delivery':
                details = f"Content sent to {log.get('recipient', 'Unknown')} - {log.get('status', 'Unknown status')}"
            elif action == 'admin_action':
                details = f"Admin: {log.get('admin', 'Unknown')} - {log.get('details', 'No details')}"
            else:
                details = str(log)
            
            log_list.append({
                'time': time_str,
                'action': action.replace('_', ' ').title(),
                'details': details
            })
        
        self.wfile.write(json.dumps({'logs': log_list}).encode())

    def serve_analytics(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        logs = self.__class__.logger.get_recent_logs(200)
        files = self.__class__.watermark_processor.get_all_processed_files()
        
        # Process data for charts
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        upload_dates = defaultdict(int)
        user_activity = defaultdict(int)
        
        for log in logs:
            if log.get('action') == 'upload':
                date = log.get('timestamp', '')
                if date:
                    try:
                        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d')
                        upload_dates[date_str] += 1
                    except:
                        pass
                
                uploader = log.get('uploader', '')
                if uploader:
                    user_activity[uploader.split('(')[0].strip()] += 1
        
        # Generate last 7 days
        dates = []
        counts = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
            counts.append(upload_dates.get(date, 0))
        
        dates.reverse()
        counts.reverse()
        
        total_size = sum(os.path.getsize(os.path.join('output', f.get('processed_filename', ''))) 
                        for f in files.values() 
                        if f.get('processed_filename') and os.path.exists(os.path.join('output', f.get('processed_filename', ''))))
        
        analytics = {
            'uploadDates': dates,
            'uploadCounts': counts,
            'userLabels': list(user_activity.keys())[:5],
            'userCounts': list(user_activity.values())[:5],
            'avgUploadsPerDay': round(sum(counts) / 7, 1),
            'mostActiveUser': max(user_activity.keys(), default='None') if user_activity else 'None',
            'totalSize': f"{total_size / 1024 / 1024:.1f} MB",
            'successRate': 95  # Placeholder
        }
        
        self.wfile.write(json.dumps(analytics).encode())

    def serve_activity(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        logs = self.__class__.logger.get_recent_logs(30)
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        daily_activity = defaultdict(int)
        
        for log in logs:
            date = log.get('timestamp', '')
            if date:
                try:
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date_str = dt.strftime('%m-%d')
                    daily_activity[date_str] += 1
                except:
                    pass
        
        # Generate last 7 days
        dates = []
        activities = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%m-%d')
            dates.append(date)
            activities.append(daily_activity.get(date, 0))
        
        dates.reverse()
        activities.reverse()
        
        activity_data = {
            'dates': dates,
            'activities': activities
        }
        
        self.wfile.write(json.dumps(activity_data).encode())

    def serve_users(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        admins = self.__class__.user_manager.get_admins()
        admin_list = [{'id': admin_id, 'added': 'Unknown'} for admin_id in admins]
        
        self.wfile.write(json.dumps({'admins': admin_list}).encode())

    def serve_file_details(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Extract watermark ID from path
        watermark_id = self.path.split('/')[-1]
        
        processed_file = self.__class__.watermark_processor.get_processed_file(watermark_id)
        if not processed_file:
            self.wfile.write(json.dumps({'error': 'File not found'}).encode())
            return
        
        logs = self.__class__.logger.get_logs_by_watermark_id(watermark_id)
        deliveries = len([log for log in logs if log.get('action') == 'delivery'])
        
        file_details = {
            'watermark_id': watermark_id,
            'filename': processed_file.get('original_filename', 'Unknown'),
            'description': processed_file.get('description', 'No description'),
            'date': processed_file.get('created_at', 'Unknown'),
            'size': 'Unknown',  # Could calculate actual size
            'deliveries': deliveries
        }
        
        self.wfile.write(json.dumps(file_details).encode())

    def handle_delete(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        watermark_id = data.get('watermark_id')
        
        try:
            # Get file info before deletion
            processed_file = self.__class__.watermark_processor.get_processed_file(watermark_id)
            if not processed_file:
                raise Exception("File not found")
            
            filename = processed_file.get('original_filename', 'Unknown file')
            processed_filename = processed_file.get('processed_filename', '')
            
            # Delete physical file
            if processed_filename:
                file_path = os.path.join('output', processed_filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Remove from database
            if watermark_id in self.__class__.watermark_processor.processed_files:
                del self.__class__.watermark_processor.processed_files[watermark_id]
                self.__class__.watermark_processor.save_processed_files()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'message': f'Deleted {filename}'}).encode())
            
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

    def handle_add_admin(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        user_input = data.get('user_input', '').strip()
        
        try:
            # Parse user mention or ID
            user_id = None
            if user_input.startswith('<@') and user_input.endswith('>'):
                user_id = int(user_input[2:-1].replace('!', ''))
            else:
                user_id = int(user_input)
            
            if self.__class__.user_manager.add_admin(user_id):
                message = f"User {user_id} is now an admin"
                success = True
            else:
                message = f"User {user_id} is already an admin"
                success = False
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': success, 'message': message}).encode())
            
        except ValueError:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'message': 'Invalid format. Use user ID or @mention'}).encode())
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'message': str(e)}).encode())

    def handle_remove_admin(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        user_id = int(data.get('user_id'))
        
        try:
            if self.__class__.user_manager.remove_admin(user_id):
                message = f"User {user_id} removed from admins"
                success = True
            else:
                message = f"User {user_id} was not an admin"
                success = False
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': success, 'message': message}).encode())
            
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'message': str(e)}).encode())

    def handle_bulk_delete(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        watermark_ids = data.get('files', [])
        deleted_count = 0
        
        try:
            for watermark_id in watermark_ids:
                processed_file = self.__class__.watermark_processor.get_processed_file(watermark_id)
                if processed_file:
                    # Delete physical file
                    processed_filename = processed_file.get('processed_filename', '')
                    if processed_filename:
                        file_path = os.path.join('output', processed_filename)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    
                    # Remove from database
                    if watermark_id in self.__class__.watermark_processor.processed_files:
                        del self.__class__.watermark_processor.processed_files[watermark_id]
                        deleted_count += 1
            
            self.__class__.watermark_processor.save_processed_files()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'deleted': deleted_count}).encode())
            
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

    def handle_export(self):
        try:
            files = self.__class__.watermark_processor.get_all_processed_files()
            logs = self.__class__.logger.get_recent_logs(1000)
            admins = self.__class__.user_manager.get_admins()
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'files': files,
                'logs': logs,
                'admins': admins,
                'stats': {
                    'total_files': len(files),
                    'total_admins': len(admins),
                    'total_logs': len(logs)
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Disposition', 'attachment; filename="bot-export.json"')
            self.end_headers()
            self.wfile.write(json.dumps(export_data, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def serve_reveals(self):
        """Serve reveals data"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            files = self.__class__.watermark_processor.get_all_processed_files()
            logs = self.__class__.logger.get_recent_logs(1000)
            
            # Calculate reveal statistics
            today = datetime.now().strftime('%Y-%m-%d')
            today_reveals = sum(1 for log in logs if log.get('timestamp', '').startswith(today) and 'reveal' in log.get('action', '').lower())
            
            # Find most popular content
            reveal_counts = {}
            for log in logs:
                if 'reveal' in log.get('action', '').lower():
                    content_id = log.get('details', '')
                    reveal_counts[content_id] = reveal_counts.get(content_id, 0) + 1
            
            popular = max(reveal_counts, key=reveal_counts.get) if reveal_counts else 'N/A'
            
            # Active reveals (recent files)
            active_reveals = []
            for file_id, file_info in files.items():
                active_reveals.append({
                    'filename': file_info.get('original_filename', 'Unknown'),
                    'clicks': reveal_counts.get(file_id, 0),
                    'created': file_info.get('created_at', '')
                })
            
            data = {
                'total': len(files),
                'today': today_reveals,
                'popular': popular,
                'active': active_reveals[:10]  # Show top 10
            }
            
            self.wfile.write(json.dumps(data).encode())
            
        except Exception as e:
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def handle_watermark_upload(self):
        """Handle watermark file upload"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            # This is a placeholder - actual file upload would need multipart handling
            response = {'success': True, 'message': 'Watermark upload feature coming soon'}
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(response).encode())
    
    def handle_watermark_settings(self):
        """Handle watermark settings update"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            settings = json.loads(post_data.decode('utf-8'))
            
            # Save settings (placeholder implementation)
            response = {'success': True, 'message': 'Settings updated'}
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        # Suppress request logs
        pass

def start_dashboard_server(port=5001):
    """Start the dashboard web server"""
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    print(f"✅ Dashboard server started on port {port}")
    print(f"   Dashboard available at: http://0.0.0.0:{port}/dashboard")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Dashboard server stopped")
        server.server_close()

if __name__ == "__main__":
    start_dashboard_server()