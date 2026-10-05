<?php
/**
 * Mijia 720p Hack - Video Recordings API
 * Author: Antigravity / Jan Sperling / Community
 */

require_once __DIR__ . '/common.php';

$mediaDir = '/tmp/sd/MIJIA_RECORD_VIDEO';
$params = get_params();
$action = isset($params['action']) ? strtolower(trim($params['action'])) : 'list';

function format_bytes($bytes) {
    if ($bytes >= 1073741824) {
        return number_format($bytes / 1073741824, 2) . ' GB';
    } elseif ($bytes >= 1048576) {
        return number_format($bytes / 1048576, 2) . ' MB';
    } elseif ($bytes >= 1024) {
        return number_format($bytes / 1024, 2) . ' KB';
    } else {
        return $bytes . ' B';
    }
}

function scan_recordings($dir, $baseDir) {
    $files = array();
    if (!is_dir($dir)) {
        return $files;
    }

    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($dir, RecursiveDirectoryIterator::SKIP_DOTS),
        RecursiveIteratorIterator::SELF_FIRST
    );

    foreach ($iterator as $item) {
        if ($item->isFile()) {
            $ext = strtolower($item->getExtension());
            if ($ext === 'mp4' || $ext === 'avi') {
                $path = $item->getPathname();
                $relPath = substr($path, strlen($baseDir));
                $relPath = ltrim($relPath, '/\\');
                $files[] = array(
                    'filename' => $item->getFilename(),
                    'path' => $relPath,
                    'url' => '/media/' . str_replace('\\', '/', $relPath),
                    'size' => $item->getSize(),
                    'size_formatted' => format_bytes($item->getSize()),
                    'mtime' => $item->getMTime(),
                    'date' => date('Y-m-d H:i:s', $item->getMTime())
                );
            }
        }
    }

    // Sort by most recent first
    usort($files, function($a, $b) {
        return $b['mtime'] - $a['mtime'];
    });

    return $files;
}

switch ($action) {
    case 'list':
        $recordings = scan_recordings($mediaDir, $mediaDir);
        send_json(array(
            'status' => 'ok',
            'count' => count($recordings),
            'recordings' => $recordings
        ));
        break;

    case 'delete':
        if (!isset($params['file'])) {
            send_error('Parameter file is required');
        }
        $rel = trim($params['file']);
        // Prevent directory traversal attacks
        if (strpos($rel, '..') !== false || strpos($rel, ':') !== false) {
            send_error('Invalid file path');
        }
        $fullPath = realpath($mediaDir . '/' . $rel);
        $realBase = realpath($mediaDir);
        if (!$fullPath || !$realBase || strpos($fullPath, $realBase) !== 0) {
            send_error('File not found or access denied', 404);
        }
        if (!unlink($fullPath)) {
            send_error('Failed to delete file', 500);
        }
        send_json(array(
            'status' => 'ok',
            'message' => 'File deleted successfully',
            'file' => $rel
        ));
        break;

    default:
        send_error("Unknown action: {$action}");
        break;
}
