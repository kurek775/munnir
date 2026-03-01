import { Component, inject, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TranslocoModule, TranslocoService } from '@jsverse/transloco';
import { AuthService } from './core/services/auth.service';
import { ThemeService } from './core/services/theme.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, TranslocoModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  protected auth = inject(AuthService);
  protected theme = inject(ThemeService);
  private transloco = inject(TranslocoService);

  ngOnInit() {
    this.theme.init();
    if (this.auth.getToken()) {
      this.auth.fetchCurrentUser();
    }
  }

  switchLang(lang: string) {
    this.transloco.setActiveLang(lang);
  }

  getActiveLang() {
    return this.transloco.getActiveLang();
  }
}
