from django.db import models

class Loja(models.Model):
    nome = models.CharField(max_length=255)
    url = models.CharField(max_length=600, default='https://exemplo.com/produto-indefinido')


    def __str__(self):
        return self.nome

class Produto(models.Model):
    nome = models.CharField(max_length=800)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    imagem = models.TextField(null=True, blank=True)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE)
    url =models.CharField(max_length=600, null=True, blank=True)
    frete = models.CharField(max_length=255, null=True, blank=True)
    prazo = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nome
class Usuario(models.Model):
    nome = models.CharField(max_length=800)
    senha = models.CharField(max_length=800)
    lojas = models.ManyToManyField(Loja)
    def __str__(self):
        return self.nome