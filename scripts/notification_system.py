#!/usr/bin/env python3
"""
Email Notification System for TFT Data Collection

Provides email notifications for:
- Weekly collection summaries
- Error alerts
- Quality warnings
- Collection failures
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailNotificationSystem:
    """
    Email notification system for TFT data collection workflow.
    
    Supports:
    - SMTP email sending
    - HTML and plain text email templates
    - Error alerts
    - Collection summaries
    - Quality warnings
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize email notification system.
        
        Args:
            config: Notification configuration dictionary
        """
        self.config = config.get('notifications', {})
        self.enabled = self.config.get('enabled', False)
        
        if not self.enabled:
            logger.info("Email notifications are disabled")
            return
        
        email_config = self.config.get('email', {})
        self.smtp_server = email_config.get('smtp_server')
        self.smtp_port = email_config.get('smtp_port', 587)
        self.use_tls = email_config.get('use_tls', True)
        self.from_address = email_config.get('from_address')
        self.to_addresses = email_config.get('to_addresses', [])
        self.username = email_config.get('username')  # For authentication
        self.password = email_config.get('password')  # For authentication
        
        # Thresholds for notifications
        thresholds = self.config.get('thresholds', {})
        self.error_count_threshold = thresholds.get('error_count', 10)
        self.quality_score_threshold = thresholds.get('quality_score', 70)
        self.critical_errors_enabled = thresholds.get('critical_errors', True)
        
        # Validate configuration
        if not self.smtp_server or not self.from_address or not self.to_addresses:
            logger.warning("Email notification configuration incomplete. Notifications disabled.")
            self.enabled = False
    
    def _send_email(self, subject: str, body_html: str, body_text: str = None) -> bool:
        """
        Send an email message.
        
        Args:
            subject: Email subject line
            body_html: HTML email body
            body_text: Plain text email body (optional, auto-generated if not provided)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Email notifications disabled, skipping email send")
            return False
        
        if not body_text:
            # Simple HTML to text conversion
            body_text = body_html.replace('<br>', '\n').replace('<br/>', '\n')
            body_text = body_text.replace('<p>', '').replace('</p>', '\n\n')
            body_text = body_text.replace('<strong>', '').replace('</strong>', '')
            body_text = body_text.replace('<em>', '').replace('</em>', '')
            # Remove remaining HTML tags
            import re
            body_text = re.sub(r'<[^>]+>', '', body_text)
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_address
            msg['To'] = ', '.join(self.to_addresses)
            
            # Add both plain text and HTML versions
            part1 = MIMEText(body_text, 'plain')
            part2 = MIMEText(body_html, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(msg)
            
            logger.info(f"Email notification sent successfully: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def send_collection_summary(self, stats: Dict[str, Any], collection_date: str = None) -> bool:
        """
        Send weekly collection summary email.
        
        Args:
            stats: Collection statistics dictionary
            collection_date: Collection date (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        collection_date = collection_date or datetime.now().strftime('%Y-%m-%d')
        
        # Extract statistics
        duration = stats.get('duration', 'N/A')
        success = stats.get('success', False)
        players = stats.get('players_collected', 0)
        matches = stats.get('matches_collected', 0)
        data_size = stats.get('data_size_mb', 0)
        quality_score = stats.get('quality_score', 0)
        total_errors = stats.get('total_errors', 0)
        files_created = stats.get('files_created', [])
        
        # Determine status
        status_icon = "[SUCCESS]" if success else "[ERROR]"
        status_text = "SUCCESS" if success else "FAILED"
        status_color = "#28a745" if success else "#dc3545"
        
        # Quality score color
        quality_color = "#28a745" if quality_score >= self.quality_score_threshold else "#ffc107" if quality_score >= 50 else "#dc3545"
        quality_grade = "PASS" if quality_score >= self.quality_score_threshold else "WARNING" if quality_score >= 50 else "FAIL"
        
        # Error summary
        errors_by_category = stats.get('errors_by_category', {})
        error_summary = ""
        if errors_by_category:
            for category, error_info in errors_by_category.items():
                count = error_info.get('count', 0)
                error_summary += f"<li><strong>{category}</strong>: {count} errors</li>"
        else:
            error_summary = "<li>No errors</li>"
        
        # HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f8f9fa; padding: 20px; }}
                .status {{ font-size: 24px; font-weight: bold; color: {status_color}; text-align: center; padding: 10px; }}
                .stats {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .stat-row {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #eee; }}
                .stat-label {{ font-weight: bold; }}
                .quality {{ background-color: {quality_color}; color: white; padding: 10px; text-align: center; border-radius: 5px; margin: 10px 0; }}
                .errors {{ background-color: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #ffc107; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎮 TFT Data Collection Summary</h1>
                    <p>Collection Date: {collection_date}</p>
                </div>
                
                <div class="content">
                    <div class="status">
                        {status_icon} Collection {status_text}
                    </div>
                    
                    <div class="stats">
                        <h3>Collection Statistics</h3>
                        <div class="stat-row">
                            <span class="stat-label">Duration:</span>
                            <span>{duration}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Players Collected:</span>
                            <span>{players:,}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Matches Collected:</span>
                            <span>{matches:,}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Data Size:</span>
                            <span>{data_size:.2f} MB</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Files Created:</span>
                            <span>{len(files_created)}</span>
                        </div>
                    </div>
                    
                    <div class="quality">
                        <h3>Quality Score: {quality_score:.2f}/100</h3>
                        <p>Status: {quality_grade}</p>
                    </div>
                    
                    <div class="errors">
                        <h3>[WARNING] Error Summary</h3>
                        <p><strong>Total Errors:</strong> {total_errors}</p>
                        <ul>
                            {error_summary}
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated message from the TFT Data Collection System</p>
                    <p>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = f"TFT Data Collection Summary - {collection_date} ({status_text})"
        return self._send_email(subject, html_body)
    
    def send_error_alert(self, error_type: str, error_details: Dict[str, Any], collection_date: str = None) -> bool:
        """
        Send error alert email.
        
        Args:
            error_type: Type of error (e.g., "rate_limit", "quality_failure", "collection_failure")
            error_details: Error details dictionary
            collection_date: Collection date (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled or not self.critical_errors_enabled:
            return False
        
        collection_date = collection_date or datetime.now().strftime('%Y-%m-%d')
        
        # Format error details
        error_info = ""
        for key, value in error_details.items():
            if isinstance(value, list) and len(value) > 10:
                value = f"{value[:10]} ... ({len(value)} total)"
            error_info += f"<li><strong>{key}:</strong> {value}</li>"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f8f9fa; padding: 20px; }}
                .alert {{ background-color: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #ffc107; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>[WARNING] TFT Data Collection Error Alert</h1>
                    <p>Collection Date: {collection_date}</p>
                </div>
                
                <div class="content">
                    <div class="alert">
                        <h2>Error Type: {error_type}</h2>
                        <ul>
                            {error_info}
                        </ul>
                    </div>
                    
                    <p><strong>Action Required:</strong> Please review the collection logs and take appropriate action.</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated alert from the TFT Data Collection System</p>
                    <p>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = f"[WARNING] TFT Collection Error Alert - {error_type} ({collection_date})"
        return self._send_email(subject, html_body)
    
    def send_quality_warning(self, quality_score: float, threshold: float, collection_date: str = None) -> bool:
        """
        Send quality score warning email.
        
        Args:
            quality_score: Current quality score
            threshold: Quality threshold
            collection_date: Collection date (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        if quality_score >= threshold:
            return False  # No warning needed
        
        collection_date = collection_date or datetime.now().strftime('%Y-%m-%d')
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #ffc107; color: #333; padding: 20px; text-align: center; }}
                .content {{ background-color: #f8f9fa; padding: 20px; }}
                .warning {{ background-color: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #ffc107; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>[WARNING] TFT Data Quality Warning</h1>
                    <p>Collection Date: {collection_date}</p>
                </div>
                
                <div class="content">
                    <div class="warning">
                        <h2>Quality Score Below Threshold</h2>
                        <p><strong>Current Score:</strong> {quality_score:.2f}/100</p>
                        <p><strong>Threshold:</strong> {threshold}/100</p>
                        <p><strong>Difference:</strong> {threshold - quality_score:.2f} points below threshold</p>
                    </div>
                    
                    <p><strong>Recommendation:</strong> Review the quality report and investigate data quality issues.</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated warning from the TFT Data Collection System</p>
                    <p>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = f"[WARNING] TFT Data Quality Warning - Score {quality_score:.2f} ({collection_date})"
        return self._send_email(subject, html_body)
    
    def should_send_error_alert(self, total_errors: int) -> bool:
        """
        Check if error alert should be sent based on threshold.
        
        Args:
            total_errors: Total number of errors
            
        Returns:
            True if alert should be sent, False otherwise
        """
        if not self.enabled:
            return False
        return total_errors >= self.error_count_threshold
    
    def should_send_quality_warning(self, quality_score: float) -> bool:
        """
        Check if quality warning should be sent.
        
        Args:
            quality_score: Current quality score
            
        Returns:
            True if warning should be sent, False otherwise
        """
        if not self.enabled:
            return False
        return quality_score < self.quality_score_threshold

