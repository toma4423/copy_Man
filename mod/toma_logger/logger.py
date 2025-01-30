import logging
import os
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom
from logging.handlers import TimedRotatingFileHandler




class TomaLogger:
    def __init__(self, log_name="application.log", log_dir="logs", level=logging.INFO, log_format="text"):
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(level)
        
        # ログディレクトリの確認と作成
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # ログのフォーマットを選択
        if log_format == "json":
            formatter = self._get_json_formatter()
        elif log_format == "xml":
            formatter = self._get_xml_formatter()
        else:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # ログファイルを日ごとにローテーション (エンコーディング指定)
        file_handler = TimedRotatingFileHandler(
            os.path.join(log_dir, log_name), when='midnight', interval=1, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)

        # コンソールへの出力
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)

        # ハンドラをロガーに追加
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _get_json_formatter(self):
        """JSON形式でログをフォーマットする"""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "timestamp": self.formatTime(record, self.datefmt),
                    "name": record.name,
                    "level": record.levelname,
                    "message": record.getMessage()
                }
                return json.dumps(log_record, ensure_ascii=False)
        return JsonFormatter()



    def _get_xml_formatter(self):
        """インデント付きのXML形式でログをフォーマットする"""
        class XmlFormatter(logging.Formatter):
            def format(self, record):
                # ログエントリを作成
                log_entry = ET.Element("entry")
                
                timestamp = ET.SubElement(log_entry, "timestamp")
                timestamp.text = self.formatTime(record, self.datefmt)
                
                name = ET.SubElement(log_entry, "name")
                name.text = record.name
                
                level = ET.SubElement(log_entry, "level")
                level.text = record.levelname
                
                message = ET.SubElement(log_entry, "message")
                message.text = record.getMessage()

                # ElementTreeのXMLを文字列に変換し、minidomで整形
                rough_string = ET.tostring(log_entry, encoding="unicode")
                reparsed = xml.dom.minidom.parseString(rough_string)
                
                # 整形されたXMLを返す（インデント付き）
                return reparsed.toprettyxml(indent="  ")

        return XmlFormatter()


    def info(self, message):
        """INFOレベルのログを記録"""
        self.logger.info(message)

    def warning(self, message):
        """WARNINGレベルのログを記録"""
        self.logger.warning(message)

    def error(self, message):
        """ERRORレベルのログを記録"""
        self.logger.error(message)

    def exception(self, message):
        """例外をキャッチしてログに記録"""
        self.logger.exception(message)
