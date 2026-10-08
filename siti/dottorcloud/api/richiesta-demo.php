<?php
// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/*
 * The site's "Richiedi una demo" form: checks what arrives and emails it to
 * NPM2. The page's script gets JSON back; a browser that posted the form by
 * itself (no JavaScript) is sent to /demo/grazie/ or /demo/errore/.
 *
 * The settings live outside the web root, in private/sito.ini beside
 * public_html on HestiaCP (or wherever SITO_CONFIG points). All optional:
 *
 *   destinatario = "info@npm2solutions.com"   who receives the requests
 *   mittente     = "sito@dottorcloud.com"      the sender: a domain whose SPF lets this server send
 *   cartella     = "/home/admin/web/dottorcloud.com/private"   where the hourly counters live
 *   archivio     = "/home/admin/web/dottorcloud.com/private/richieste-demo.jsonl"
 *                  every request also written here, one JSON per line (off when empty)
 */

declare(strict_types=1);

const DEFAULT_TO = 'info@npm2solutions.com';
const MAX_PER_HOUR = 5;
const MIN_MILLISECONDS = 3000;

// name => [label in the email, required?, longest, what to say when it is missing]
const FIELDS = [
	'nome' => ['Nome e cognome', true, 100, 'Scrivi il tuo nome.'],
	'centro' => ['Centro', true, 150, 'Scrivi il nome del centro.'],
	'email' => ['Email', true, 200, 'Scrivi la tua email.'],
	'telefono' => ['Telefono', true, 40, 'Scrivi un numero di telefono.'],
	'tipo' => ['Tipo di centro', false, 60, ''],
	'professionisti' => ['Professionisti', false, 10, ''],
	'citta' => ['Città', false, 100, ''],
	'messaggio' => ['Cosa vorrebbe vedere', false, 3000, ''],
];
const TYPES = ['Poliambulatorio', 'Studio medico', 'Fisioterapia e riabilitazione', 'Nutrizione', 'Altro'];
const SIZES = ['1', '2-3', '4-8', '9-15', '16+'];

function settings(): array
{
	$file = getenv('SITO_CONFIG') ?: dirname(__DIR__, 2) . '/private/sito.ini';
	$ini = is_readable($file) ? (parse_ini_file($file) ?: []) : [];
	$host = preg_replace('/^www\./', '', strtolower($_SERVER['SERVER_NAME'] ?? 'localhost'));
	$host = preg_replace('/[^a-z0-9.-]/', '', $host) ?: 'localhost';
	return [
		'to' => trim((string) ($ini['destinatario'] ?? DEFAULT_TO)),
		'from' => trim((string) ($ini['mittente'] ?? "sito@{$host}")),
		'dir' => trim((string) ($ini['cartella'] ?? dirname($file))),
		'archive' => trim((string) ($ini['archivio'] ?? '')),
	];
}

function wants_json(): bool
{
	return str_contains($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json');
}

function finish(int $status, array $answer, string $page): never
{
	header('Cache-Control: no-store');
	if (wants_json()) {
		http_response_code($status);
		header('Content-Type: application/json; charset=utf-8');
		echo json_encode($answer, JSON_UNESCAPED_UNICODE);
	} else {
		header('Location: ' . $page, true, 303);
	}
	exit;
}

/** One line of text, or the message with its new lines: no control characters either way. */
function clean(string $value, bool $multiline): string
{
	$value = str_replace(["\r\n", "\r"], "\n", $value);
	$value = preg_replace($multiline ? '/[^\P{C}\n]/u' : '/\p{C}/u', ' ', $value);
	if ($value === null) {
		return ''; // not UTF-8
	}
	if (!$multiline) {
		$value = preg_replace('/\s+/u', ' ', $value) ?? '';
	}
	return trim($value);
}

/** @return array{0: array<string, string>, 1: array<string, string>} the data and what is wrong with it */
function validate(array $input): array
{
	$data = [];
	$errors = [];
	foreach (FIELDS as $name => [$label, $required, $longest, $missing]) {
		$raw = $input[$name] ?? '';
		$value = is_string($raw) ? clean($raw, $name === 'messaggio') : '';
		if ($value === '') {
			if ($required) {
				$errors[$name] = $missing;
			}
			continue;
		}
		if (mb_strlen($value) > $longest) {
			$errors[$name] = "Al massimo {$longest} caratteri.";
			continue;
		}
		$data[$name] = $value;
	}
	if (isset($data['email']) && !filter_var($data['email'], FILTER_VALIDATE_EMAIL)) {
		$errors['email'] = "Controlla l'indirizzo email.";
	}
	if (
		isset($data['telefono']) &&
		(!preg_match('/^\+?[0-9 ().\/-]+$/', $data['telefono']) || preg_match_all('/\d/', $data['telefono']) < 6)
	) {
		$errors['telefono'] = 'Controlla il numero di telefono.';
	}
	if (isset($data['tipo']) && !in_array($data['tipo'], TYPES, true)) {
		$errors['tipo'] = 'Scegli una delle voci.';
	}
	if (isset($data['professionisti']) && !in_array($data['professionisti'], SIZES, true)) {
		$errors['professionisti'] = 'Scegli una delle voci.';
	}
	if (($input['privacy'] ?? '') !== '1') {
		$errors['privacy'] = "Spunta la casella dopo aver letto l'informativa.";
	}
	return [$data, $errors];
}

/** At most MAX_PER_HOUR requests an hour from one address; the addresses are kept hashed, for an hour. */
function too_many(string $dir, string $address): bool
{
	if ($address === '' || !is_dir($dir) || !is_writable($dir)) {
		return false;
	}
	$handle = @fopen($dir . '/richieste-demo-contatori.json', 'c+');
	if (!$handle) {
		return false;
	}
	flock($handle, LOCK_EX);
	$now = time();
	$seen = json_decode(stream_get_contents($handle) ?: '{}', true);
	$seen = is_array($seen) ? $seen : [];
	foreach ($seen as $key => $times) {
		$times = array_values(array_filter((array) $times, fn($time) => is_int($time) && $time > $now - 3600));
		if ($times) {
			$seen[$key] = $times;
		} else {
			unset($seen[$key]);
		}
	}
	$key = hash('sha256', $address);
	$blocked = count($seen[$key] ?? []) >= MAX_PER_HOUR;
	if (!$blocked) {
		$seen[$key][] = $now;
	}
	ftruncate($handle, 0);
	rewind($handle);
	fwrite($handle, json_encode($seen));
	fflush($handle);
	flock($handle, LOCK_UN);
	fclose($handle);
	return $blocked;
}

/** A name for From or Reply-To: quoted when plain ASCII, as encoded words otherwise. */
function display_name(string $name): string
{
	if (preg_match('/[^\x20-\x7e]/', $name)) {
		return mb_encode_mimeheader($name, 'UTF-8', 'Q');
	}
	return '"' . addcslashes($name, '"\\') . '"';
}

function send(array $settings, array $data): bool
{
	$lines = ['Nuova richiesta di demo dal sito di DottorCloud.', ''];
	foreach (FIELDS as $name => [$label]) {
		if (!isset($data[$name])) {
			continue;
		}
		$lines[] = $name === 'messaggio' ? "\n{$label}:\n{$data[$name]}" : "{$label}: {$data[$name]}";
	}
	$lines[] = '';
	$lines[] = 'Arrivata il ' . date('d/m/Y \a\l\l\e H:i') . '. Rispondendo a questa email si scrive a chi l\'ha mandata.';

	$from = filter_var($settings['from'], FILTER_VALIDATE_EMAIL) ? $settings['from'] : DEFAULT_TO;
	$headers = [
		'From' => display_name('Sito DottorCloud') . " <{$from}>",
		'Reply-To' => display_name($data['nome']) . " <{$data['email']}>",
		'MIME-Version' => '1.0',
		'Content-Type' => 'text/plain; charset=UTF-8',
		'Content-Transfer-Encoding' => '8bit',
	];
	$subject = mb_encode_mimeheader("Richiesta demo: {$data['centro']}", 'UTF-8');
	return mail($settings['to'], $subject, implode("\n", $lines), $headers, '-f' . $from);
}

function archive(string $file, array $data): bool
{
	if ($file === '') {
		return false;
	}
	$line = json_encode(['arrivata' => date('c')] + $data, JSON_UNESCAPED_UNICODE) . "\n";
	return @file_put_contents($file, $line, FILE_APPEND | LOCK_EX) !== false;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
	header('Allow: POST');
	http_response_code(405);
	exit;
}

date_default_timezone_set('Europe/Rome');
mb_internal_encoding('UTF-8');
$settings = settings();

// the trap filled in, or the form sent in a blink: say all went well, send nothing
$trap = $_POST['sito_web'] ?? '';
$elapsed = $_POST['t'] ?? '';
if (
	(is_string($trap) && $trap !== '') ||
	(is_string($elapsed) && ctype_digit($elapsed) && (int) $elapsed < MIN_MILLISECONDS)
) {
	finish(200, ['ok' => true], '/demo/grazie/');
}

[$data, $errors] = validate($_POST);
if ($errors) {
	finish(422, ['ok' => false, 'errori' => $errors, 'messaggio' => 'Controlla i campi segnati.'], '/demo/errore/');
}

if (too_many($settings['dir'], $_SERVER['REMOTE_ADDR'] ?? '')) {
	finish(
		429,
		['ok' => false, 'messaggio' => "Sono arrivate troppe richieste da questa connessione. Riprova tra un'ora, o scrivici all'indirizzo in questa pagina."],
		'/demo/errore/'
	);
}

$archived = archive($settings['archive'], $data);
$sent = send($settings, $data);
if (!$sent) {
	error_log('richiesta-demo: the email could not be handed to the mail server' . ($archived ? ' (kept in the archive)' : ''));
}
if (!$sent && !$archived) {
	finish(
		500,
		['ok' => false, 'messaggio' => "Non siamo riusciti a inviare la richiesta. Riprova tra poco, o scrivici all'indirizzo in questa pagina."],
		'/demo/errore/'
	);
}

finish(200, ['ok' => true], '/demo/grazie/');
