import {Component, OnInit} from '@angular/core';
import {Router} from "@angular/router";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  constructor(
     protected router: Router) { }

  ngOnInit() {
    document.getElementById("logout").style.display = "none";
    document.getElementById("login").style.display = "none";
  }

  navigateLogin() {
     this.router.navigateByUrl('/auth/login').then(() => {
      window.location.reload();
    });
  }

  navigateHome() {
    this.router.navigateByUrl('/pages').then();
  }
}
