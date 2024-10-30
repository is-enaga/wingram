"""
Module to run commands on terminal.

added: 2024/07/19
"""
from .log import logger
import subprocess

def linux(command, verbose=False):
    logger.info(f"run: {command}")
    try:
        # コマンドの実行
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            # 成功時のログ出力
            if verbose:
                logger.info(f'{stdout.decode()}')
            return stdout.decode()
        else:
            # エラー時のログ出力
            if verbose:
                logger.error(f'Error code: {process.returncode}\nError: {stderr.decode()}')
            return stderr.decode()
        
    except Exception as e:
        logger.error(f'Failed to execute command "{command}". Exception: {str(e)}')