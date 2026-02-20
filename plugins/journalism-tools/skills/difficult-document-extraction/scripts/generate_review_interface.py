#!/usr/bin/env python3
"""
Generate a self-contained HTML review interface for document extraction.

Embeds page images (as base64) and extracted data into a single HTML file
that journalists can open in any browser to review, edit, and approve extractions.
"""

import argparse
import base64
import json
import sys
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Review: {document_name}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.5;
        }}
        
        .header {{
            background: #1a1a2e;
            color: white;
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        
        .header h1 {{
            font-size: 1.25rem;
            font-weight: 500;
        }}
        
        .header-controls {{
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .progress-bar {{
            background: #333;
            border-radius: 4px;
            height: 8px;
            width: 200px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            background: #4ade80;
            height: 100%;
            transition: width 0.3s ease;
        }}
        
        .progress-text {{
            font-size: 0.875rem;
            color: #aaa;
        }}
        
        .btn {{
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .btn-primary {{
            background: #3b82f6;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #2563eb;
        }}
        
        .btn-success {{
            background: #22c55e;
            color: white;
        }}
        
        .btn-success:hover {{
            background: #16a34a;
        }}
        
        .btn-secondary {{
            background: #e5e5e5;
            color: #333;
        }}
        
        .btn-secondary:hover {{
            background: #d4d4d4;
        }}
        
        .btn-outline {{
            background: transparent;
            border: 1px solid #555;
            color: white;
        }}
        
        .btn-outline:hover {{
            background: rgba(255,255,255,0.1);
        }}
        
        .main-container {{
            display: flex;
            height: calc(100vh - 60px);
        }}
        
        .sidebar {{
            width: 280px;
            background: white;
            border-right: 1px solid #e5e5e5;
            overflow-y: auto;
            flex-shrink: 0;
        }}
        
        .sidebar-header {{
            padding: 1rem;
            border-bottom: 1px solid #e5e5e5;
            font-weight: 600;
            color: #666;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .page-list {{
            list-style: none;
        }}
        
        .page-item {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }}
        
        .page-item:hover {{
            background: #f9f9f9;
        }}
        
        .page-item.active {{
            background: #eff6ff;
            border-left: 3px solid #3b82f6;
        }}
        
        .page-item.approved {{
            background: #f0fdf4;
        }}
        
        .page-item.edited {{
            background: #fefce8;
        }}
        
        .page-name {{
            font-weight: 500;
        }}
        
        .page-status {{
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        }}
        
        .status-pending {{
            background: #f3f4f6;
            color: #6b7280;
        }}
        
        .status-approved {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .status-edited {{
            background: #fef9c3;
            color: #854d0e;
        }}
        
        .content-area {{
            flex: 1;
            display: flex;
            overflow: hidden;
        }}
        
        .panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }}
        
        .panel-header {{
            padding: 1rem;
            background: white;
            border-bottom: 1px solid #e5e5e5;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .panel-content {{
            flex: 1;
            overflow: auto;
            padding: 1rem;
        }}
        
        .image-panel .panel-content {{
            background: #1a1a1a;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 1rem;
        }}
        
        .page-image {{
            max-width: 100%;
            max-height: calc(100vh - 180px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        
        .divider {{
            width: 6px;
            background: #e5e5e5;
            cursor: col-resize;
            flex-shrink: 0;
        }}
        
        .divider:hover {{
            background: #3b82f6;
        }}
        
        .data-panel {{
            background: #fafafa;
        }}
        
        .record-card {{
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .record-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #e5e5e5;
        }}
        
        .record-title {{
            font-weight: 600;
            color: #333;
        }}
        
        .field-row {{
            display: flex;
            margin-bottom: 0.5rem;
            align-items: flex-start;
        }}
        
        .field-label {{
            width: 140px;
            flex-shrink: 0;
            font-size: 0.875rem;
            color: #666;
            padding-top: 0.5rem;
        }}
        
        .field-value {{
            flex: 1;
        }}
        
        .field-input {{
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #e5e5e5;
            border-radius: 4px;
            font-size: 0.875rem;
            font-family: inherit;
        }}
        
        .field-input:focus {{
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }}
        
        .field-input.edited {{
            background: #fefce8;
            border-color: #eab308;
        }}
        
        textarea.field-input {{
            min-height: 80px;
            resize: vertical;
        }}
        
        .field-note {{
            font-size: 0.75rem;
            color: #999;
            margin-top: 0.25rem;
        }}
        
        .field-note.redacted {{
            color: #dc2626;
        }}
        
        .field-note.uncertain {{
            color: #d97706;
        }}
        
        .action-bar {{
            padding: 1rem;
            background: white;
            border-top: 1px solid #e5e5e5;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }}
        
        .zoom-controls {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }}
        
        .zoom-controls button {{
            width: 32px;
            height: 32px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
        }}
        
        .zoom-controls button:hover {{
            background: #f5f5f5;
        }}
        
        .zoom-level {{
            font-size: 0.875rem;
            color: #666;
            min-width: 50px;
            text-align: center;
        }}
        
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 200;
        }}
        
        .modal-overlay.active {{
            display: flex;
        }}
        
        .modal {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }}
        
        .modal h2 {{
            margin-bottom: 1rem;
        }}
        
        .modal-actions {{
            display: flex;
            gap: 1rem;
            justify-content: flex-end;
            margin-top: 1.5rem;
        }}
        
        .export-options {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        
        .export-option {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem;
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .export-option:hover {{
            border-color: #3b82f6;
            background: #f8fafc;
        }}
        
        .export-option input {{
            width: 18px;
            height: 18px;
        }}
        
        .export-option-text {{
            flex: 1;
        }}
        
        .export-option-title {{
            font-weight: 500;
        }}
        
        .export-option-desc {{
            font-size: 0.875rem;
            color: #666;
        }}
        
        .keyboard-hint {{
            font-size: 0.75rem;
            color: #999;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e5e5e5;
        }}
        
        kbd {{
            background: #f3f4f6;
            padding: 0.125rem 0.375rem;
            border-radius: 3px;
            font-size: 0.75rem;
            border: 1px solid #d1d5db;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: #666;
        }}
        
        .empty-state-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        @media (max-width: 1200px) {{
            .sidebar {{
                width: 220px;
            }}
        }}
        
        @media (max-width: 900px) {{
            .main-container {{
                flex-direction: column;
            }}
            
            .sidebar {{
                width: 100%;
                max-height: 200px;
            }}
            
            .content-area {{
                flex-direction: column;
            }}
            
            .panel {{
                min-height: 300px;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>📄 {document_name}</h1>
        <div class="header-controls">
            <div class="progress-text">
                <span id="approved-count">0</span> / <span id="total-count">0</span> approved
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
            </div>
            <button class="btn btn-outline" onclick="showExportModal()">Export</button>
            <button class="btn btn-success" id="finish-btn" onclick="finishReview()">Finish Review</button>
        </div>
    </header>
    
    <div class="main-container">
        <nav class="sidebar">
            <div class="sidebar-header">Pages</div>
            <ul class="page-list" id="page-list"></ul>
        </nav>
        
        <div class="content-area">
            <div class="panel image-panel">
                <div class="panel-header">
                    <span>Original Document</span>
                    <div class="zoom-controls">
                        <button onclick="zoomOut()">−</button>
                        <span class="zoom-level" id="zoom-level">100%</span>
                        <button onclick="zoomIn()">+</button>
                        <button onclick="resetZoom()">↺</button>
                    </div>
                </div>
                <div class="panel-content">
                    <img id="page-image" class="page-image" src="" alt="Document page">
                </div>
            </div>
            
            <div class="divider" id="divider"></div>
            
            <div class="panel data-panel">
                <div class="panel-header">
                    <span>Extracted Data</span>
                    <span id="edit-indicator" style="font-size: 0.875rem; color: #666;"></span>
                </div>
                <div class="panel-content" id="data-content"></div>
                <div class="action-bar">
                    <div>
                        <button class="btn btn-secondary" onclick="revertChanges()">Revert Changes</button>
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn btn-secondary" onclick="prevPage()">← Previous</button>
                        <button class="btn btn-primary" onclick="approveAndNext()">Approve & Next →</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="modal-overlay" id="export-modal">
        <div class="modal">
            <h2>Export Reviewed Data</h2>
            <div class="export-options">
                <label class="export-option">
                    <input type="radio" name="export-type" value="approved" checked>
                    <div class="export-option-text">
                        <div class="export-option-title">Approved records only</div>
                        <div class="export-option-desc">Export only pages you've approved</div>
                    </div>
                </label>
                <label class="export-option">
                    <input type="radio" name="export-type" value="all">
                    <div class="export-option-text">
                        <div class="export-option-title">All records</div>
                        <div class="export-option-desc">Export everything, with approval status marked</div>
                    </div>
                </label>
                <label class="export-option">
                    <input type="radio" name="export-type" value="changes">
                    <div class="export-option-text">
                        <div class="export-option-title">Changes log</div>
                        <div class="export-option-desc">Export only fields you edited, showing before/after</div>
                    </div>
                </label>
            </div>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="hideExportModal()">Cancel</button>
                <button class="btn btn-primary" onclick="exportData()">Download JSON</button>
            </div>
        </div>
    </div>
    
    <script>
        // Embedded data
        const DOCUMENT_NAME = {document_name_json};
        const PAGES = {pages_json};
        const EXTRACTED_DATA = {extracted_data_json};
        const SCHEMA = {schema_json};
        
        // State
        let currentPageIndex = 0;
        let pageStatus = {{}};  // pageNum -> 'pending' | 'approved' | 'edited'
        let editedData = JSON.parse(JSON.stringify(EXTRACTED_DATA));  // Deep copy
        let originalData = JSON.parse(JSON.stringify(EXTRACTED_DATA));
        let zoomLevel = 100;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            initializePageStatus();
            renderPageList();
            selectPage(0);
            updateProgress();
            setupKeyboardShortcuts();
            setupResizer();
        }});
        
        function initializePageStatus() {{
            PAGES.forEach((page, index) => {{
                pageStatus[index] = 'pending';
            }});
        }}
        
        function renderPageList() {{
            const list = document.getElementById('page-list');
            list.innerHTML = PAGES.map((page, index) => `
                <li class="page-item ${{currentPageIndex === index ? 'active' : ''}} ${{pageStatus[index]}}" 
                    onclick="selectPage(${{index}})" data-index="${{index}}">
                    <span class="page-name">${{page.name}}</span>
                    <span class="page-status status-${{pageStatus[index]}}">${{pageStatus[index]}}</span>
                </li>
            `).join('');
        }}
        
        function selectPage(index) {{
            currentPageIndex = index;
            const page = PAGES[index];
            
            // Update image
            document.getElementById('page-image').src = page.image;
            
            // Update active state in list
            document.querySelectorAll('.page-item').forEach((item, i) => {{
                item.classList.toggle('active', i === index);
            }});
            
            // Render data for this page
            renderDataPanel();
        }}
        
        function renderDataPanel() {{
            const content = document.getElementById('data-content');
            const pageNum = currentPageIndex + 1;
            
            // Find records for this page
            const records = editedData.records.filter(r => r.source_page === pageNum);
            
            if (records.length === 0) {{
                content.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📋</div>
                        <p>No extracted records for this page</p>
                    </div>
                `;
                return;
            }}
            
            content.innerHTML = records.map((record, recordIndex) => {{
                const globalIndex = editedData.records.findIndex(r => r === record);
                return renderRecordCard(record, globalIndex);
            }}).join('');
            
            updateEditIndicator();
        }}
        
        function renderRecordCard(record, globalIndex) {{
            const fields = Object.entries(record)
                .filter(([key]) => !key.startsWith('_'))  // Skip internal fields
                .map(([key, value]) => renderField(key, value, globalIndex));
            
            return `
                <div class="record-card" data-record-index="${{globalIndex}}">
                    <div class="record-header">
                        <span class="record-title">Record #${{globalIndex + 1}}</span>
                    </div>
                    ${{fields.join('')}}
                </div>
            `;
        }}
        
        function renderField(key, value, recordIndex) {{
            const originalRecord = originalData.records[recordIndex];
            const originalValue = originalRecord ? originalRecord[key] : value;
            const isEdited = JSON.stringify(value) !== JSON.stringify(originalValue);
            
            // Check for associated notes
            const noteKey = key + '_note';
            const statusKey = key + '_status';
            const confidenceKey = key + '_confidence';
            
            const record = editedData.records[recordIndex];
            const note = record[noteKey];
            const status = record[statusKey];
            const confidence = record[confidenceKey];
            
            let noteHtml = '';
            if (note) {{
                const noteClass = note.toLowerCase().includes('redact') ? 'redacted' : 
                                  (confidence === 'low' || confidence === 'uncertain') ? 'uncertain' : '';
                noteHtml = `<div class="field-note ${{noteClass}}">📝 ${{note}}</div>`;
            }}
            if (status && status !== 'present') {{
                noteHtml += `<div class="field-note ${{status === 'redacted' ? 'redacted' : ''}}">Status: ${{status}}</div>`;
            }}
            if (confidence && confidence !== 'high') {{
                noteHtml += `<div class="field-note uncertain">Confidence: ${{confidence}}</div>`;
            }}
            
            const displayValue = value === null ? '' : (typeof value === 'object' ? JSON.stringify(value) : value);
            const inputType = typeof value === 'number' ? 'number' : 'text';
            const isLongText = typeof value === 'string' && value.length > 100;
            
            const inputHtml = isLongText ? 
                `<textarea class="field-input ${{isEdited ? 'edited' : ''}}" 
                    data-record="${{recordIndex}}" data-field="${{key}}"
                    onchange="updateField(${{recordIndex}}, '${{key}}', this.value)">${{displayValue}}</textarea>` :
                `<input type="${{inputType}}" class="field-input ${{isEdited ? 'edited' : ''}}" 
                    value="${{String(displayValue).replace(/"/g, '&quot;')}}"
                    data-record="${{recordIndex}}" data-field="${{key}}"
                    onchange="updateField(${{recordIndex}}, '${{key}}', this.value)">`;
            
            return `
                <div class="field-row">
                    <label class="field-label">${{formatFieldName(key)}}</label>
                    <div class="field-value">
                        ${{inputHtml}}
                        ${{noteHtml}}
                    </div>
                </div>
            `;
        }}
        
        function formatFieldName(key) {{
            return key.replace(/_/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase());
        }}
        
        function updateField(recordIndex, field, value) {{
            const record = editedData.records[recordIndex];
            const originalRecord = originalData.records[recordIndex];
            
            // Type coercion
            if (typeof originalRecord[field] === 'number') {{
                value = value === '' ? null : Number(value);
            }} else if (value === '') {{
                value = null;
            }}
            
            record[field] = value;
            
            // Update status
            if (pageStatus[currentPageIndex] !== 'approved') {{
                pageStatus[currentPageIndex] = 'edited';
            }}
            
            renderPageList();
            updateEditIndicator();
            
            // Mark the input as edited
            const input = document.querySelector(`[data-record="${{recordIndex}}"][data-field="${{field}}"]`);
            if (input) {{
                const isEdited = JSON.stringify(value) !== JSON.stringify(originalRecord[field]);
                input.classList.toggle('edited', isEdited);
            }}
        }}
        
        function updateEditIndicator() {{
            const indicator = document.getElementById('edit-indicator');
            const pageNum = currentPageIndex + 1;
            const records = editedData.records.filter(r => r.source_page === pageNum);
            
            let editCount = 0;
            records.forEach((record, i) => {{
                const globalIndex = editedData.records.indexOf(record);
                const original = originalData.records[globalIndex];
                if (JSON.stringify(record) !== JSON.stringify(original)) {{
                    editCount++;
                }}
            }});
            
            indicator.textContent = editCount > 0 ? `${{editCount}} record(s) modified` : '';
        }}
        
        function approveAndNext() {{
            pageStatus[currentPageIndex] = 'approved';
            renderPageList();
            updateProgress();
            
            if (currentPageIndex < PAGES.length - 1) {{
                selectPage(currentPageIndex + 1);
            }}
        }}
        
        function prevPage() {{
            if (currentPageIndex > 0) {{
                selectPage(currentPageIndex - 1);
            }}
        }}
        
        function revertChanges() {{
            const pageNum = currentPageIndex + 1;
            editedData.records.forEach((record, index) => {{
                if (record.source_page === pageNum) {{
                    editedData.records[index] = JSON.parse(JSON.stringify(originalData.records[index]));
                }}
            }});
            
            if (pageStatus[currentPageIndex] === 'edited') {{
                pageStatus[currentPageIndex] = 'pending';
            }}
            
            renderDataPanel();
            renderPageList();
        }}
        
        function updateProgress() {{
            const approved = Object.values(pageStatus).filter(s => s === 'approved').length;
            const total = PAGES.length;
            
            document.getElementById('approved-count').textContent = approved;
            document.getElementById('total-count').textContent = total;
            document.getElementById('progress-fill').style.width = `${{(approved / total) * 100}}%`;
        }}
        
        // Zoom controls
        function zoomIn() {{
            zoomLevel = Math.min(200, zoomLevel + 25);
            applyZoom();
        }}
        
        function zoomOut() {{
            zoomLevel = Math.max(50, zoomLevel - 25);
            applyZoom();
        }}
        
        function resetZoom() {{
            zoomLevel = 100;
            applyZoom();
        }}
        
        function applyZoom() {{
            const img = document.getElementById('page-image');
            img.style.transform = `scale(${{zoomLevel / 100}})`;
            img.style.transformOrigin = 'top center';
            document.getElementById('zoom-level').textContent = `${{zoomLevel}}%`;
        }}
        
        // Resizable panels
        function setupResizer() {{
            const divider = document.getElementById('divider');
            let isResizing = false;
            
            divider.addEventListener('mousedown', (e) => {{
                isResizing = true;
                document.body.style.cursor = 'col-resize';
            }});
            
            document.addEventListener('mousemove', (e) => {{
                if (!isResizing) return;
                
                const container = document.querySelector('.content-area');
                const containerRect = container.getBoundingClientRect();
                const percentage = ((e.clientX - containerRect.left) / containerRect.width) * 100;
                
                const imagePanel = document.querySelector('.image-panel');
                const dataPanel = document.querySelector('.data-panel');
                
                imagePanel.style.flex = `0 0 ${{Math.max(20, Math.min(80, percentage))}}%`;
                dataPanel.style.flex = '1';
            }});
            
            document.addEventListener('mouseup', () => {{
                isResizing = false;
                document.body.style.cursor = '';
            }});
        }}
        
        // Keyboard shortcuts
        function setupKeyboardShortcuts() {{
            document.addEventListener('keydown', (e) => {{
                // Don't trigger if typing in an input
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                
                switch(e.key) {{
                    case 'ArrowRight':
                    case 'j':
                        e.preventDefault();
                        if (currentPageIndex < PAGES.length - 1) selectPage(currentPageIndex + 1);
                        break;
                    case 'ArrowLeft':
                    case 'k':
                        e.preventDefault();
                        if (currentPageIndex > 0) selectPage(currentPageIndex - 1);
                        break;
                    case 'Enter':
                        if (e.metaKey || e.ctrlKey) {{
                            e.preventDefault();
                            approveAndNext();
                        }}
                        break;
                    case '=':
                    case '+':
                        e.preventDefault();
                        zoomIn();
                        break;
                    case '-':
                        e.preventDefault();
                        zoomOut();
                        break;
                    case 'e':
                        if (e.metaKey || e.ctrlKey) {{
                            e.preventDefault();
                            showExportModal();
                        }}
                        break;
                }}
            }});
        }}
        
        // Export functionality
        function showExportModal() {{
            document.getElementById('export-modal').classList.add('active');
        }}
        
        function hideExportModal() {{
            document.getElementById('export-modal').classList.remove('active');
        }}
        
        function exportData() {{
            const exportType = document.querySelector('input[name="export-type"]:checked').value;
            let exportContent;
            let filename;
            
            switch(exportType) {{
                case 'approved':
                    const approvedPages = Object.entries(pageStatus)
                        .filter(([_, status]) => status === 'approved')
                        .map(([index, _]) => parseInt(index) + 1);
                    
                    exportContent = {{
                        export_metadata: {{
                            source_document: DOCUMENT_NAME,
                            export_date: new Date().toISOString(),
                            export_type: 'approved_only',
                            approved_pages: approvedPages,
                            total_pages: PAGES.length
                        }},
                        records: editedData.records.filter(r => approvedPages.includes(r.source_page))
                    }};
                    filename = `${{DOCUMENT_NAME}}_approved.json`;
                    break;
                    
                case 'all':
                    exportContent = {{
                        export_metadata: {{
                            source_document: DOCUMENT_NAME,
                            export_date: new Date().toISOString(),
                            export_type: 'all_records',
                            page_status: Object.fromEntries(
                                Object.entries(pageStatus).map(([i, s]) => [parseInt(i) + 1, s])
                            )
                        }},
                        records: editedData.records.map((record, index) => ({{
                            ...record,
                            _review_status: pageStatus[record.source_page - 1] || 'pending'
                        }}))
                    }};
                    filename = `${{DOCUMENT_NAME}}_all.json`;
                    break;
                    
                case 'changes':
                    const changes = [];
                    editedData.records.forEach((record, index) => {{
                        const original = originalData.records[index];
                        Object.keys(record).forEach(key => {{
                            if (JSON.stringify(record[key]) !== JSON.stringify(original[key])) {{
                                changes.push({{
                                    record_index: index,
                                    source_page: record.source_page,
                                    field: key,
                                    original_value: original[key],
                                    new_value: record[key]
                                }});
                            }}
                        }});
                    }});
                    
                    exportContent = {{
                        export_metadata: {{
                            source_document: DOCUMENT_NAME,
                            export_date: new Date().toISOString(),
                            export_type: 'changes_only',
                            total_changes: changes.length
                        }},
                        changes: changes
                    }};
                    filename = `${{DOCUMENT_NAME}}_changes.json`;
                    break;
            }}
            
            downloadJSON(exportContent, filename);
            hideExportModal();
        }}
        
        function downloadJSON(data, filename) {{
            const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
        
        function finishReview() {{
            const approved = Object.values(pageStatus).filter(s => s === 'approved').length;
            const pending = Object.values(pageStatus).filter(s => s === 'pending').length;
            
            if (pending > 0) {{
                if (!confirm(`You have ${{pending}} page(s) still pending review. Export anyway?`)) {{
                    return;
                }}
            }}
            
            showExportModal();
        }}
        
        // Close modal on outside click
        document.getElementById('export-modal').addEventListener('click', (e) => {{
            if (e.target === e.currentTarget) {{
                hideExportModal();
            }}
        }});
    </script>
</body>
</html>"""


def encode_image(image_path: Path) -> str:
    """Encode image to base64 data URI."""
    suffix = image_path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix, "image/png")

    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{data}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate a self-contained HTML review interface"
    )
    parser.add_argument(
        "pages_dir",
        type=Path,
        help="Directory containing page images (page_001.png, etc.)",
    )
    parser.add_argument(
        "extracted_json", type=Path, help="JSON file with extracted data"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output HTML file (default: review_interface.html)",
    )
    parser.add_argument(
        "--schema",
        "-s",
        type=Path,
        default=None,
        help="Optional schema JSON file for field metadata",
    )
    parser.add_argument(
        "--document-name",
        "-n",
        type=str,
        default=None,
        help="Document name for display (default: from JSON metadata)",
    )
    args = parser.parse_args()

    # Validate inputs
    if not args.pages_dir.is_dir():
        print(f"Error: Pages directory not found: {args.pages_dir}", file=sys.stderr)
        sys.exit(1)

    if not args.extracted_json.exists():
        print(
            f"Error: Extracted JSON not found: {args.extracted_json}", file=sys.stderr
        )
        sys.exit(1)

    # Load extracted data
    with open(args.extracted_json) as f:
        extracted_data = json.load(f)

    # Get document name
    document_name = args.document_name
    if not document_name:
        if "extraction_metadata" in extracted_data:
            document_name = extracted_data["extraction_metadata"].get(
                "source_document", "Document"
            )
        else:
            document_name = args.extracted_json.stem

    # Load page images
    image_files = sorted(args.pages_dir.glob("page_*.png")) + sorted(
        args.pages_dir.glob("page_*.jpg")
    )
    if not image_files:
        print(f"Error: No page images found in {args.pages_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(image_files)} page images")

    # Build pages data with embedded images
    pages = []
    for i, img_path in enumerate(image_files, 1):
        print(f"  Encoding page {i}...")
        pages.append(
            {"name": f"Page {i}", "image": encode_image(img_path), "page_num": i}
        )

    # Load schema if provided
    schema = {}
    if args.schema and args.schema.exists():
        with open(args.schema) as f:
            schema = json.load(f)

    # Generate HTML
    html_content = HTML_TEMPLATE.format(
        document_name=document_name,
        document_name_json=json.dumps(document_name),
        pages_json=json.dumps(pages),
        extracted_data_json=json.dumps(extracted_data),
        schema_json=json.dumps(schema),
    )

    # Write output
    output_path = args.output or Path(f"review_{document_name.replace(' ', '_')}.html")
    with open(output_path, "w") as f:
        f.write(html_content)

    print(f"\n✅ Review interface generated: {output_path}")
    print("   Open this file in any web browser to review the extraction.")
    print("\n   Keyboard shortcuts:")
    print("   • ← → or j/k : Navigate pages")
    print("   • Ctrl/Cmd + Enter : Approve and go to next")
    print("   • +/- : Zoom in/out")
    print("   • Ctrl/Cmd + E : Export")


if __name__ == "__main__":
    main()
