#!/usr/bin/env python

"""
Automated Backup Solution
Backs up specified directories to local/remote locations
Supports compression, encryption, and cloud storage
Generates detailed backup reports
"""

import os
import sys
import argparse
import hashlib
import datetime
import json
import tarfile
import zipfile
import subprocess
from pathlib import Path
import logging

class BackupManager:
    def __init__(self, config_file=None):
        # Setup logging FIRST
        self.setup_logging()
        
        self.config = {
            'backup_sources': [],
            'backup_destinations': [],
            'compression': 'tar.gz',
            'encryption': False,
            'encryption_key': None,
            'retention_days': 30,
            'exclude_patterns': ['.tmp', '.log', '.cache'],
            'notify_email': None,
            'cloud_storage': None
        }
        
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path.home() / '.backup_manager'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'backup.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                self.config.update(user_config)
            self.logger.info(f"✅ Configuration loaded from {config_file}")
        except Exception as e:
            self.logger.error(f"❌ Error loading config: {e}")

    def save_config(self, config_file):
        """Save configuration to JSON file"""
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"✅ Configuration saved to {config_file}")
        except Exception as e:
            self.logger.error(f"❌ Error saving config: {e}")

    def validate_paths(self):
        """Validate source and destination paths"""
        errors = []
        
        # Check source directories
        for source in self.config['backup_sources']:
            if not os.path.exists(source):
                errors.append(f"Source path does not exist: {source}")
            elif not os.path.isdir(source):
                errors.append(f"Source path is not a directory: {source}")
        
        # Check destination directories
        for destination in self.config['backup_destinations']:
            dest_path = Path(destination)
            if not dest_path.parent.exists():
                errors.append(f"Destination parent path does not exist: {destination}")
        
        return errors

    def calculate_directory_size(self, path):
        """Calculate total size of directory in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if not os.path.islink(filepath):  # Skip symlinks
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass  # Skip files we can't access
        return total_size

    def should_exclude(self, filepath):
        """Check if file should be excluded from backup"""
        filename = os.path.basename(filepath)
        for pattern in self.config['exclude_patterns']:
            if pattern in filename:
                return True
        return False

    def create_backup_archive(self, source_dirs, backup_path):
        """Create compressed backup archive"""
        self.logger.info(f"📦 Creating backup archive: {backup_path}")
        
        try:
            if self.config['compression'] == 'zip':
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for source_dir in source_dirs:
                        for root, dirs, files in os.walk(source_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                if not self.should_exclude(file_path):
                                    arcname = os.path.relpath(file_path, start=source_dir)
                                    zipf.write(file_path, arcname)
            
            else:  # tar.gz by default
                with tarfile.open(backup_path, 'w:gz') as tar:
                    for source_dir in source_dirs:
                        for root, dirs, files in os.walk(source_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                if not self.should_exclude(file_path):
                                    arcname = os.path.relpath(file_path, start=source_dir)
                                    tar.add(file_path, arcname=arcname)
            
            # Calculate checksum
            file_hash = self.calculate_checksum(backup_path)
            self.logger.info(f"✅ Backup created successfully: {backup_path}")
            self.logger.info(f"🔐 Checksum: {file_hash}")
            
            return True, file_hash
            
        except Exception as e:
            self.logger.error(f"❌ Error creating backup: {e}")
            return False, None

    def calculate_checksum(self, filepath):
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def encrypt_backup(self, filepath, key=None):
        """Encrypt backup file using GPG"""
        if not self.config['encryption']:
            return True
            
        encryption_key = key or self.config['encryption_key']
        if not encryption_key:
            self.logger.warning("⚠️  Encryption enabled but no key provided")
            return False
        
        try:
            encrypted_file = filepath + '.gpg'
            cmd = [
                'gpg', '--batch', '--yes', '--passphrase', encryption_key,
                '--symmetric', '--cipher-algo', 'AES256',
                '--output', encrypted_file, filepath
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                os.remove(filepath)  # Remove unencrypted version
                self.logger.info(f"🔒 Backup encrypted: {encrypted_file}")
                return True
            else:
                self.logger.error(f"❌ Encryption failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Encryption error: {e}")
            return False

    def cleanup_old_backups(self, backup_dir):
        """Remove backups older than retention period"""
        self.logger.info("🧹 Cleaning up old backups...")
        
        retention_days = self.config['retention_days']
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=retention_days)
        
        deleted_count = 0
        try:
            for item in Path(backup_dir).iterdir():
                if item.is_file():
                    stat = item.stat()
                    file_time = datetime.datetime.fromtimestamp(stat.st_mtime)
                    
                    if file_time < cutoff_time:
                        item.unlink()
                        deleted_count += 1
                        self.logger.info(f"🗑️  Deleted old backup: {item.name}")
            
            self.logger.info(f"✅ Cleanup completed: {deleted_count} files deleted")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup error: {e}")

    def sync_to_cloud(self, filepath):
        """Sync backup to cloud storage"""
        cloud_config = self.config.get('cloud_storage')
        if not cloud_config:
            return True
            
        try:
            if cloud_config.get('type') == 's3':
                # AWS S3 sync
                cmd = [
                    'aws', 's3', 'cp', filepath,
                    f"s3://{cloud_config['bucket']}/{Path(filepath).name}"
                ]
                
            elif cloud_config.get('type') == 'gcs':
                # Google Cloud Storage sync
                cmd = [
                    'gsutil', 'cp', filepath,
                    f"gs://{cloud_config['bucket']}/{Path(filepath).name}"
                ]
            
            else:
                self.logger.warning(f"⚠️  Unsupported cloud type: {cloud_config.get('type')}")
                return False
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"☁️  Backup synced to cloud: {filepath}")
                return True
            else:
                self.logger.error(f"❌ Cloud sync failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Cloud sync error: {e}")
            return False

    def generate_report(self, success, backup_path, checksum, start_time, errors=None):
        """Generate detailed backup report"""
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        
        report = {
            'timestamp': end_time.isoformat(),
            'success': success,
            'backup_file': backup_path,
            'checksum': checksum,
            'duration_seconds': duration.total_seconds(),
            'sources_backed_up': self.config['backup_sources'],
            'destinations_used': self.config['backup_destinations'],
            'compression': self.config['compression'],
            'encryption': self.config['encryption'],
            'errors': errors or []
        }
        
        # Save report to file
        report_file = Path.home() / '.backup_manager' / 'latest_report.json'
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 BACKUP REPORT")
        print("="*60)
        print(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"Backup File: {backup_path}")
        print(f"Checksum: {checksum}")
        print(f"Duration: {duration}")
        print(f"Sources: {', '.join(self.config['backup_sources'])}")
        
        if errors:
            print(f"Errors: {chr(10).join(errors)}")
        
        print(f"Full report: {report_file}")
        print("="*60)
        
        return report

    def run_backup(self):
        """Execute the complete backup process"""
        self.logger.info("🚀 Starting backup process...")
        start_time = datetime.datetime.now()
        
        # Validate paths
        validation_errors = self.validate_paths()
        if validation_errors:
            self.logger.error("❌ Validation errors:")
            for error in validation_errors:
                self.logger.error(f"   {error}")
            self.generate_report(False, None, None, start_time, validation_errors)
            return False
        
        # Calculate total size
        total_size = 0
        for source in self.config['backup_sources']:
            size = self.calculate_directory_size(source)
            total_size += size
            self.logger.info(f"📁 Source: {source} (Size: {size / (1024**3):.2f} GB)")
        
        self.logger.info(f"💾 Total backup size: {total_size / (1024**3):.2f} GB")
        
        # Create backup for each destination
        success = True
        backup_path = None
        checksum = None
        errors = []
        
        for destination in self.config['backup_destinations']:
            try:
                # Create backup filename with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}.{self.config['compression']}"
                backup_path = os.path.join(destination, backup_name)
                
                # Create backup archive
                archive_success, checksum = self.create_backup_archive(
                    self.config['backup_sources'], backup_path
                )
                
                if not archive_success:
                    errors.append(f"Failed to create archive in {destination}")
                    success = False
                    continue
                
                # Encrypt if enabled
                if self.config['encryption']:
                    encrypt_success = self.encrypt_backup(backup_path)
                    if not encrypt_success:
                        errors.append(f"Encryption failed for {destination}")
                        success = False
                        continue
                
                # Sync to cloud if configured
                if self.config.get('cloud_storage'):
                    cloud_success = self.sync_to_cloud(backup_path)
                    if not cloud_success:
                        errors.append(f"Cloud sync failed for {destination}")
                        # Don't mark as complete failure for cloud issues
                
                # Cleanup old backups
                self.cleanup_old_backups(destination)
                
            except Exception as e:
                errors.append(f"Error in {destination}: {str(e)}")
                success = False
        
        # Generate report
        report = self.generate_report(success, backup_path, checksum, start_time, errors)
        
        if success:
            self.logger.info("🎉 Backup completed successfully!")
        else:
            self.logger.error("💥 Backup completed with errors")
        
        return success

def create_sample_config():
    """Create a sample configuration file"""
    sample_config = {
        "backup_sources": [
            "./test_documents",
            "./test_projects"
        ],
        "backup_destinations": [
            "./backups"
        ],
        "compression": "tar.gz",
        "encryption": False,
        "encryption_key": "your-secret-key-here",
        "retention_days": 7,
        "exclude_patterns": [".tmp", ".log", ".cache", "node_modules"],
        "notify_email": None,
        "cloud_storage": None
    }
    
    config_file = "backup_config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    return config_file

def main():
    parser = argparse.ArgumentParser(description='Automated Backup Solution')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--source', '-s', action='append', help='Source directory to backup')
    parser.add_argument('--destination', '-d', action='append', help='Backup destination')
    parser.add_argument('--create-config', action='store_true', help='Create sample configuration file')
    parser.add_argument('--dry-run', action='store_true', help='Validate without actual backup')
    
    args = parser.parse_args()
    
    if args.create_config:
        config_file = create_sample_config()
        print(f"✅ Sample configuration created: {config_file}")
        print("📝 Please edit the configuration file before use.")
        return
    
    # Initialize backup manager
    backup_mgr = BackupManager(args.config)
    
    # Override config with command line arguments
    if args.source:
        backup_mgr.config['backup_sources'] = args.source
    if args.destination:
        backup_mgr.config['backup_destinations'] = args.destination
    
    if args.dry_run:
        print("🔍 DRY RUN - Validating configuration...")
        errors = backup_mgr.validate_paths()
        if errors:
            print("❌ Validation errors:")
            for error in errors:
                print(f"   {error}")
        else:
            print("✅ Configuration is valid")
            total_size = 0
            for source in backup_mgr.config['backup_sources']:
                size = backup_mgr.calculate_directory_size(source)
                total_size += size
                print(f"📁 {source}: {size / (1024**3):.2f} GB")
            print(f"💾 Total estimated size: {total_size / (1024**3):.2f} GB")
        return
    
    # Run backup
    success = backup_mgr.run_backup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()