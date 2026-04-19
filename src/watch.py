#!/usr/bin/env python3
"""
Watch mode - Automaattinen analyysi uusille tiedostoille
Monitoroi input_folder-kansiota ja analysoi uudet tiedostot automaattisesti
"""
import os
import time
import sys
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import main analyzer
try:
    from src.main import AudioQualityAnalyzer
except ImportError:
    logger.error("Virhe: src.main ei löydy. Varmista että olet projektin juurikansiossa.")
    sys.exit(1)


class FileWatcher:
    """Monitor directory and analyze new audio files"""
    
    def __init__(self, watch_dir: str = "input_folder", 
                 output_dir: str = "output",
                 check_interval: int = 10):
        self.watch_dir = Path(watch_dir)
        self.output_dir = Path(output_dir)
        self.check_interval = check_interval
        self.processed_files = set()
        
        # Ensure directories exist
        self.watch_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize analyzer
        logger.info("Alustetaan analysaattori...")
        self.analyzer = AudioQualityAnalyzer()
        
        # Load already processed files
        self._load_processed_files()
        
    def _load_processed_files(self):
        """Load list of already processed files"""
        processed_file = self.output_dir / ".processed_files.txt"
        if processed_file.exists():
            with open(processed_file, 'r', encoding='utf-8') as f:
                self.processed_files = set(line.strip() for line in f if line.strip())
            logger.info(f"Ladattu {len(self.processed_files)} aiempaa tiedostoa")
    
    def _save_processed_file(self, filename: str):
        """Save processed file to list"""
        self.processed_files.add(filename)
        processed_file = self.output_dir / ".processed_files.txt"
        with open(processed_file, 'a', encoding='utf-8') as f:
            f.write(f"{filename}\n")
    
    def _get_audio_files(self):
        """Get all audio files in watch directory"""
        audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}
        files = []
        for ext in audio_extensions:
            files.extend(self.watch_dir.glob(f"*{ext}"))
            files.extend(self.watch_dir.glob(f"*{ext.upper()}"))
        return files
    
    def _analyze_file(self, filepath: Path):
        """Analyze single audio file"""
        try:
            logger.info(f"📊 Analysoidaan: {filepath.name}")
            start_time = time.time()
            
            # Analyze
            results = self.analyzer.analyze_file(str(filepath))
            
            # Export results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_prefix = self.output_dir / f"{filepath.stem}_{timestamp}"
            
            self.analyzer.export_results(results, str(output_prefix))
            
            elapsed = time.time() - start_time
            
            # Log summary
            logger.info(f"✅ Valmis {elapsed:.1f}s: {filepath.name}")
            logger.info(f"   📈 Kokonaislaatu: {results['overall_score']:.1f}/100")
            
            if results.get('issues'):
                logger.info(f"   ⚠️  Löydettiin {len(results['issues'])} ongelmaa")
            
            # Mark as processed
            self._save_processed_file(str(filepath.relative_to(self.watch_dir)))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Virhe analysoitaessa {filepath.name}: {e}")
            return False
    
    def watch(self):
        """Main watch loop"""
        logger.info(f"👀 Monitoroidaan kansiota: {self.watch_dir.absolute()}")
        logger.info(f"📁 Tulokset tallentaan: {self.output_dir.absolute()}")
        logger.info(f"⏱️  Tarkistusväli: {self.check_interval}s")
        logger.info("Paina Ctrl+C lopettaaksesi\n")
        
        try:
            while True:
                # Find new files
                audio_files = self._get_audio_files()
                new_files = [
                    f for f in audio_files 
                    if str(f.relative_to(self.watch_dir)) not in self.processed_files
                ]
                
                if new_files:
                    logger.info(f"🆕 Löydettiin {len(new_files)} uutta tiedostoa")
                    for filepath in new_files:
                        self._analyze_file(filepath)
                    logger.info("")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Watcher pysäytetty")
            logger.info(f"📊 Yhteensä analysoitu: {len(self.processed_files)} tiedostoa")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automaattinen äänenlaatuanalysaattori - Watch Mode"
    )
    parser.add_argument(
        '--input', '-i',
        default='input_folder',
        help='Monitoroitava kansio (oletus: input_folder)'
    )
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Tuloskansio (oletus: output)'
    )
    parser.add_argument(
        '--interval', '-t',
        type=int,
        default=10,
        help='Tarkistusväli sekunneissa (oletus: 10)'
    )
    
    args = parser.parse_args()
    
    # Create and run watcher
    watcher = FileWatcher(
        watch_dir=args.input,
        output_dir=args.output,
        check_interval=args.interval
    )
    
    watcher.watch()


if __name__ == "__main__":
    main()
