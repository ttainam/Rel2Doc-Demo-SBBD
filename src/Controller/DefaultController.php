<?php

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

class DefaultController extends AbstractController
{
    #[Route('/favicon', name: 'favicon')]
    public function favicon()
    {
        $response = new Response(file_get_contents($this->getParameter('kernel.project_dir').'/postgresql-icon.png'));
        $response->headers->set('Content-Type', 'image/x-icon');
        return $response;
    }
}
