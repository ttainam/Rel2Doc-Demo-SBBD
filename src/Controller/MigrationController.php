<?php

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Process\Exception\ProcessFailedException;
use Symfony\Component\Process\Process;
use Symfony\Component\Routing\Attribute\Route;

class MigrationController extends AbstractController
{
    #[Route('/migration', name: 'app_migration')]
    public function index(): Response
    {
        return $this->render('migration/index.html', [
            'controller_name' => 'MigrationController',
        ]);
    }

    #[Route('/join-tables', name: 'join_tables', methods: ['POST'])]
    public function joinTables(Request $request): Response
    {
        ini_set('max_execution_time', 600);
        ini_set('memory_limit', '-1');
        $data =  json_decode($request->getContent(), true);

        $this->replaceValues($data);
        $scriptPath = $this->getParameter('kernel.project_dir') . '/pyFiles/main.py';

        $process = new Process(['/usr/bin/python3', $scriptPath]);
        $process->setTimeout(null);
        $process->setWorkingDirectory($this->getParameter('kernel.project_dir') . '/pyFiles');

        try {
            $process->mustRun();
            $process->getOutput();
        } catch (ProcessFailedException $exception) {
            return new Response('Erro ao executar o script Python: ' . $exception->getMessage(), 500);
        }

        return new JsonResponse(['message' => 'Migração conclúida com sucesso!'], Response::HTTP_OK);
    }

    private function replaceValues($data)
    {
        $templatePath = $this->getParameter('kernel.project_dir') . '/pyFiles/config_template.py';
        $configContent = file_get_contents($templatePath);

        $configContent = str_replace('dbname_value', $data['pgDbname'], $configContent);
        $configContent = str_replace('user_value', $data['pgUser'], $configContent);
        $configContent = str_replace('password_value', $data['pgPassword'], $configContent);
        $configContent = str_replace('host_value', $data['pgHost'], $configContent);
        $configContent = str_replace('MONGOHOST', $data['mongoHost'], $configContent);
        $configContent = str_replace(27014, $data['mongoPort'], $configContent);
        $configContent = str_replace('MONGODBNAME', $data['mongoDbname'], $configContent);
        $configContent = str_replace('INSERT_OBJECT_ID_REFERENCES_VALUE', $data['insertObjectIdReferences'] == 'on' ? True : False, $configContent);
        $configContent = str_replace('INSERT_NULL_FIELDS_VALUE', $data['insertNullFields'] == 'on' ? True : False, $configContent);
        
        $newConfigPath = $this->getParameter('kernel.project_dir') . '/pyFiles/config.py';

        if(file_exists($newConfigPath)) {
            unlink($newConfigPath);
        }

        file_put_contents($newConfigPath, $configContent);
    }
}
