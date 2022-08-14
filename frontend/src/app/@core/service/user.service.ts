import {GlobalVariable} from "../global";
import {HttpClient, HttpParams} from "@angular/common/http";
import { Injectable } from "@angular/core";
import {Observable} from "rxjs";
import {Schema} from "../model/user.model";

@Injectable()
export class UserService {
  private baseApiUrl = GlobalVariable.BASE_API_URL;
  private baseUserId = GlobalVariable.BASE_USER_ID;

  constructor(private http: HttpClient) { }

  getSchemaList(userId: string): Observable<Schema[]> {
    let id = userId;
    if (id === '') {
      id = this.baseUserId;
    }

    const params = new HttpParams()
      .set('userId',id);
    return this.http.get<Schema[]>(this.baseApiUrl + 'schemaList',
      {
        params: params
      });
  }
}
