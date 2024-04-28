import {Injectable} from "@angular/core";
import {Observable} from "rxjs";
import {HttpClient, HttpHeaders, HttpParams} from "@angular/common/http";
import {GlobalVariable} from "../global";

@Injectable()
export class CommonService {
  private baseApiUrl = GlobalVariable.BASE_API_URL;

  constructor(private http: HttpClient) { }

/**
 * 获取2个字符串的相似度
 * @param {string} str1 字符串1
 * @param {string} str2 字符串2
 * @returns {number} 相似度
 */
  getSimilarity(str1,str2) {
    let sameNum = 0
    //寻找相同字符
    for (let i = 0; i < str1.length; i++) {
        for(let j =0;j<str2.length;j++){
            if(str1[i]===str2[j]){
                sameNum ++
                break
            }
        }
    }
    // console.log(str1,str2);
    // console.log("相似度",(sameNum/str1.length) * 100);
    //判断2个字符串哪个长度比较长
    let length = str1.length > str2.length ? str1.length : str2.length
    return (sameNum/length) * 100 || 0
  }

  uploadFiles(schemaId: string, type: string, selectedFile:File[]): Observable<string> {
    let fd = new FormData();
    for (let i = 0; i < selectedFile.length; i++) {
      fd.append(selectedFile[i].name, selectedFile[i])
    }

    return this.http.post<string>(this.baseApiUrl + 'uploadFiles/' + schemaId + '/' + type, fd);
  }

  schemaMining(filesPath: string, schemaId: string, minSupport: number, patternMin: number, patternMax: number, token: any[]): Observable<any> {
    const params = new HttpParams()
      .set('files_path', filesPath)
      .set('schemaId', schemaId)
      .set('minSupport', minSupport.toString())
      .set('patternMin', patternMin.toString())
      .set('patternMax', patternMax.toString())
      .set('ignoreTokens',JSON.stringify(token).toString());
    return this.http.post<any>(this.baseApiUrl + 'schemaMining', params);
  }

  readTextFileOfPDF(filesPath: string, filename: string, filetype: string):  Observable<string> {
    const params = new HttpParams()
      .set('files_path', filesPath)
      .set('filename', filename)
      .set('filetype', filetype);
    return this.http.get<string>(this.baseApiUrl + 'readTextFileOfPDF',
    {
      params: params
    });
  }
}
