<?php

declare(strict_types=1);

namespace OrderBillingSystem\Infrastructure\Database;

use PDO;
use PDOException;
use RuntimeException;

/**
 * Conexão Segura com Banco de Dados via PDO.
 * Camadas de proteção:
 * 1. Força PDO::ATTR_EMULATE_PREPARES => false (previne SQL Injection no driver).
 * 2. Trata PDOException mascarando DSN, usuário e senha da mensagem de erro e do stack trace.
 * 3. Encoraja execução parametrizada nativa.
 */
final class SafeDatabaseConnection
{
    private ?PDO $pdo = null;

    public function __construct(private readonly DatabaseConfig $config)
    {
    }

    public function getPdo(): PDO
    {
        if ($this->pdo === null) {
            $this->connect();
        }
        return $this->pdo;
    }

    private function connect(): void
    {
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::ATTR_PERSISTENT => false,
        ];

        try {
            $this->pdo = new PDO(
                $this->config->getDsn(),
                $this->config->getUser(),
                $this->config->getPassword(),
                $options
            );
        } catch (PDOException $e) {
            // CAMADA DE SEGURANÇA: Sanitização de exceção
            // Remove qualquer vestígio de senha ou host interno antes de propagar o erro
            throw new RuntimeException(
                "Database connection error [ERR_DB_AUTHENTICATION_OR_NETWORK]. Details redacted for security.",
                500
            );
        }
    }

    /**
     * Executa query usando exclusivamente prepared statements.
     */
    public function executePrepared(string $sql, array $params = []): array
    {
        $stmt = $this->getPdo()->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll();
    }
}
