<?php

declare(strict_types=1);

namespace OrderBillingSystem\Infrastructure\Database;

use InvalidArgumentException;

/**
 * Configuração Segura de Banco de Dados.
 * - Carrega credenciais exclusivamente de variáveis de ambiente.
 * - Implementa __debugInfo() para NUNCA exibir a senha em var_dump(), print_r() ou logs.
 */
final readonly class DatabaseConfig
{
    public string $driver;
    public string $host;
    public int $port;
    public string $database;
    public string $user;
    private string $password;

    public function __construct(
        ?string $host = null,
        ?string $database = null,
        ?string $user = null,
        ?string $password = null,
        ?int $port = null,
        ?string $driver = null
    ) {
        $this->driver = $driver ?? (getenv('DB_DRIVER') ?: 'sqlsrv');
        $this->host = $host ?? (getenv('DB_HOST') ?: '');
        $this->database = $database ?? (getenv('DB_NAME') ?: '');
        $this->user = $user ?? (getenv('DB_USER') ?: '');
        $this->password = $password ?? (getenv('DB_PASSWORD') ?: '');
        $this->port = $port ?? (int) (getenv('DB_PORT') ?: 1433);

        if (trim($this->host) === '' || trim($this->database) === '' || trim($this->user) === '') {
            throw new InvalidArgumentException('Database host, name and user must be configured via the environment.');
        }
    }

    public function getDsn(): string
    {
        if ($this->driver === 'sqlite') {
            return "sqlite:{$this->database}";
        }
        return "{$this->driver}:host={$this->host};port={$this->port};dbname={$this->database};charset=utf8mb4";
    }

    public function getUser(): string
    {
        return $this->user;
    }

    public function getPassword(): string
    {
        return $this->password;
    }

    /**
     * CAMADA DE SEGURANÇA: Mascaramento ativo de credenciais.
     * Retorna array seguro quando inspecionado em debug/logs.
     */
    public function __debugInfo(): array
    {
        return [
            'driver' => $this->driver,
            'host' => $this->host,
            'port' => $this->port,
            'database' => $this->database,
            'user' => $this->user,
            'password' => '******** (REDACTED)',
        ];
    }
}
